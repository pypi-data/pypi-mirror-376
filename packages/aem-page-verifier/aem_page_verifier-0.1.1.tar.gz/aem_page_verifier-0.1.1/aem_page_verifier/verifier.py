import argparse
import json
import logging
import os
import sys
import requests


class AEMPageVerifier:
    """A class to compare AEM publish pages with the author server."""

    def __init__(self, config_file, root_path, batch_size=1000, timeout=30):
        """
        Initialize the verifier.

        Args:
            config_file (str): Path to the JSON configuration file.
            root_path (str): Root JCR path to query (e.g., /content/myroot).
            batch_size (int, optional): Number of paths per batch. Defaults to 1000.
            timeout (int, optional): Request timeout in seconds. Defaults to 30.
        """
        logging.basicConfig(
            filename='path_check.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

        self.config = self._load_config(config_file)
        self.root_path = root_path
        self.batch_size = batch_size
        self.timeout = timeout
        self.base_url = f"{self.config['author_url']}/bin/querybuilder.json"
        self.auth = (self.config['author_user'], self.config['author_pass'])

    def _load_config(self, config_file):
        """
        Load configuration from a JSON file or environment variables.

        Args:
            config_file (str): Path to the JSON configuration file.

        Returns:
            dict: Configuration dictionary.

        Raises:
            FileNotFoundError: If the config file does not exist and env vars are incomplete.
            KeyError: If required config keys are missing.
        """
        config = {}
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)

        # Override with environment variables if available
        config['publish_url'] = os.getenv('AEM_PUBLISH_URL', config.get('publish_url'))
        config['author_url'] = os.getenv('AEM_AUTHOR_URL', config.get('author_url'))
        config['publish_user'] = os.getenv('AEM_PUBLISH_USER', config.get('publish_user'))
        config['publish_pass'] = os.getenv('AEM_PUBLISH_PASS', config.get('publish_pass'))
        config['author_user'] = os.getenv('AEM_AUTHOR_USER', config.get('author_user'))
        config['author_pass'] = os.getenv('AEM_AUTHOR_PASS', config.get('author_pass'))
        config['batch_size'] = int(os.getenv('AEM_BATCH_SIZE', config.get('batch_size', 500)))
        config['timeout'] = int(os.getenv('AEM_TIMEOUT', config.get('timeout', 30)))

        required_keys = ['publish_url', 'author_url', 'publish_user', 'publish_pass',
                         'author_user', 'author_pass', 'batch_size']
        for key in required_keys:
            if not config.get(key):
                raise KeyError(f"Missing required config key: {key}")

        return config

    def get_pages_from_publish(self):
        """
        Query the AEM publish server for all cq:Page paths under the root path.

        Returns:
            list: List of page paths from the publish tier.
        """
        query_url = f"{self.config['publish_url']}/bin/querybuilder.json"
        offset = 0
        all_paths = []

        while True:
            params = {
                'path': self.root_path,
                'type': 'cq:Page',
                'p.limit': str(self.batch_size),
                'p.offset': str(offset),
                'p.hits': 'selective',
                'p.properties': 'jcr:path'
            }
            try:
                response = requests.get(
                    query_url,
                    params=params,
                    auth=(self.config['publish_user'], self.config['publish_pass']),
                    timeout=self.timeout
                )
                if response.status_code != 200:
                    raise Exception(f"Failed to query publish server: {response.status_code} - {response.text}")

                data = response.json()
                hits = data.get('hits', [])
                if not hits:
                    break

                paths = [hit['jcr:path'] for hit in hits]
                all_paths.extend(paths)
                offset += self.batch_size
                logging.info(f"Collected {len(all_paths)} pages so far...")

                if len(hits) < self.batch_size:
                    break

            except Exception as e:
                logging.error(f"Error querying publish server: {e}")
                raise

        return all_paths

    def _build_query_params(self, batch_paths):
        """Build Query Builder parameters for a batch of paths."""
        params = {
            "group.p.or": "true",
            "p.limit": "-1",
            "p.hits": "selective",
            "p.properties": "jcr:path"
        }
        for i, path in enumerate(batch_paths, start=1):
            params[f"group.{i}_path"] = path
            params[f"group.{i}_path.exact"] = "true"
        return params

    def _query_batch_post(self, batch_paths):
        """Execute a Query Builder POST request for a batch of paths."""
        data = self._build_query_params(batch_paths)
        result = set()
        query_url = f"{self.config['author_url']}/bin/querybuilder.json"
        try:
            response = requests.post(query_url, auth=self.auth, data=data, timeout=self.timeout)
            logging.info(f"Query length: {len(data)}")
            if response.status_code == 200:
                json_result = response.json()
                success = json_result['success']
                num_results = json_result['results']
                more = json_result['more']
                offset = json_result['offset']
                hits = json_result['hits']
                logging.info(f"Processed batch: success={success} : num={num_results} : more={more} : offset={offset}")
                for hit in hits:
                    result.add(hit["jcr:path"])
                return result
            else:
                logging.error(f"POST query failed for batch: {query_url} : {data} : {response.status_code}:{response.text}")
                return result
        except requests.exceptions.Timeout:
            logging.error(f"Timeout querying batch of {len(batch_paths)} paths")
            return result
        except Exception as e:
            logging.error(f"Error querying batch: {e}")
            return result

    def check_pages_on_author(self, paths):
        """Check if pages from publish exist on the author tier."""
        missing_paths = set()
        for i in range(0, len(paths), self.batch_size):
            batch = paths[i:i + self.batch_size]
            logging.info(f"Processing batch {i // self.batch_size + 1} with {len(batch)} paths")
            verified_list = self._query_batch_post(batch)
            if len(batch) > len(verified_list):
                missing_paths.update(set(batch) - verified_list)
        return missing_paths

    def run(self):
        """Execute the page verification process."""
        try:
            logging.info(f"Querying publish server for pages under {self.root_path}...")
            publish_paths = self.get_pages_from_publish()
            logging.info(f"Found {len(publish_paths)} pages on publish.")

            if not publish_paths:
                logging.info("No pages found on publish server.")
                return True

            logging.info("\nChecking page existence on author server...")
            missing_paths = self.check_pages_on_author(publish_paths)
            if missing_paths:
                logging.info("\nMissing pages on author server:")
                for path in missing_paths:
                    logging.info(path)
                logging.info(f"\nTotal ghost pages: {len(missing_paths)}")
            else:
                logging.info("\nAll pages from publish exist on author.")
            return True

        except Exception as e:
            logging.error(f"Error: {str(e)}")
            return False


def main():
    """Parse command-line arguments and run the AEMPageVerifier."""
    parser = argparse.ArgumentParser(description="Compare AEM publish pages with author server.")
    parser.add_argument('--root_path', required=True, help='Root JCR path to query (e.g., /content/myroot)')
    parser.add_argument('--config_file', default='config.json', help='Path to JSON config file (default: config.json)')

    args = parser.parse_args()

    verifier = AEMPageVerifier(args.config_file, args.root_path)
    success = verifier.run()
    sys.exit(0 if success else 1)