import json
import sys
import time
import argparse
import os
from alpha_expression_miner import AlphaExpressionMiner
from loguru import logger


class ContinuousAlphaExpressionMiner:
    def __init__(self, credentials_path, ollama_url=None, mining_interval=6):
        self.miner = AlphaExpressionMiner(credentials_path)
        self.ollama_url = ollama_url
        self.mining_interval = mining_interval * 3600  # Convert hours to seconds
        self.hopeful_alphas_file = 'hopeful_alphas.json'

    def get_hopeful_alphas(self):
        """Read alphas from hopeful_alphas.json"""
        try:
            if os.path.exists(self.hopeful_alphas_file):
                with open(self.hopeful_alphas_file, 'r') as f:
                    data = json.load(f)
                    return data.get('alphas', [])
            else:
                logger.warning(f"File {self.hopeful_alphas_file} not found")
                return []
        except Exception as e:
            logger.error(f"Error reading {self.hopeful_alphas_file}: {e}")
            return []

    def mine_alpha_expression(self, expression):
        """Mine variations of a single alpha expression"""
        try:
            logger.info(f"Starting mining for expression: {expression}")

            # Parse expression and get parameters
            parameters = self.miner.parse_expression(expression)

            if not parameters:
                logger.info(f"No parameters found for expression: {expression}")
                return False

            # Select all parameters for variation
            selected_params = parameters
            logger.info(f"Selected {len(selected_params)} parameters for variation")

            # Get ranges and steps for selected parameters
            selected_params = self.miner.get_parameter_ranges(selected_params, auto_mode=True)

            # Generate variations
            variations = self.miner.generate_variations(expression, selected_params)
            logger.info(f"Generated {len(variations)} variations")

            # Test variations
            results = []
            total = len(variations)
            for i, var in enumerate(variations, 1):
                logger.info(f"Testing variation {i}/{total}: {var}")
                result = self.miner.test_alpha(var)
                if result["status"] == "success":
                    logger.info(f"Successful test for: {var}")
                    results.append({
                        "expression": var,
                        "result": result["result"]
                    })
                else:
                    logger.error(f"Failed to test variation: {var}")
                    logger.error(f"Error: {result['message']}")

            # Save results
            if results:
                timestamp = int(time.time())
                output_file = f'mined_expressions_{timestamp}.json'
                logger.info(f"Saving {len(results)} results to {output_file}")
                with open(output_file, 'w') as f:
                    json.dump(results, f, indent=2)

            # Remove the mined alpha from hopeful_alphas.json
            logger.info("Mining completed, removing alpha from hopeful_alphas.json")
            removed = self.miner.remove_alpha_from_hopeful(expression)
            if removed:
                logger.info(f"Successfully removed alpha '{expression}' from hopeful_alphas.json")
            else:
                logger.warning(f"Could not remove alpha '{expression}' from hopeful_alphas.json")

            return True

        except Exception as e:
            logger.error(f"Error mining expression {expression}: {e}")
            return False

    def run_continuous_mining(self):
        """Run continuous mining of alpha expressions"""
        logger.info(f"Starting continuous alpha expression mining with {self.mining_interval/3600}h intervals")

        while True:
            try:
                # Get hopeful alphas
                hopeful_alphas = self.get_hopeful_alphas()

                if not hopeful_alphas:
                    logger.info("No hopeful alphas found, waiting for next cycle...")
                    time.sleep(self.mining_interval)
                    continue

                logger.info(f"Found {len(hopeful_alphas)} hopeful alphas to mine")

                # Process each alpha
                for alpha in hopeful_alphas:
                    try:
                        success = self.mine_alpha_expression(alpha)
                        if success:
                            logger.info(f"Successfully mined alpha: {alpha}")
                        else:
                            logger.warning(f"Failed to mine alpha: {alpha}")

                        # Small delay between alphas
                        time.sleep(10)

                    except Exception as e:
                        logger.error(f"Error processing alpha {alpha}: {e}")
                        continue

                logger.info(f"Mining cycle completed, waiting {self.mining_interval/3600} hours before next cycle...")
                time.sleep(self.mining_interval)

            except KeyboardInterrupt:
                logger.info("Received interrupt signal, stopping continuous mining...")
                break
            except Exception as e:
                logger.error(f"Error in continuous mining cycle: {e}")
                logger.info("Waiting 5 minutes before retrying...")
                time.sleep(300)

def main():
    parser = argparse.ArgumentParser(description='Continuous Alpha Expression Miner')
    parser.add_argument('--credentials', type=str, default='./credential.txt',
                      help='Path to credentials file (default: ./credential.txt)')
    parser.add_argument('--ollama-url', type=str, default='http://localhost:11434',
                      help='Ollama API URL (default: http://localhost:11434)')
    parser.add_argument('--mining-interval', type=int, default=6,
                      help='Mining interval in hours (default: 6)')
    parser.add_argument('--log-level', type=str, default='INFO',
                      choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                      help='Set the logging level (default: INFO)')

    args = parser.parse_args()

    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level=args.log_level)

    try:
        miner = ContinuousAlphaExpressionMiner(
            args.credentials,
            args.ollama_url,
            args.mining_interval
        )
        miner.run_continuous_mining()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    main()