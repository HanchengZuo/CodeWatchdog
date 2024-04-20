import subprocess


class BanditAnalyzer():

    def run_bandit_analysis(self, file_path, added_line_numbers):
        """Runs Bandit analysis and filters results based on added lines."""
        bandit_results = self.analyze_file_with_bandit(file_path)
        filtered_results = self.filter_bandit_results(
            bandit_results, added_line_numbers)
        print("Filtered Bandit results:")
        for result in filtered_results:
            print(result)

    def analyze_file_with_bandit(self, file_path):
        """Executes Bandit security analysis and returns the result."""
        result = subprocess.run(['bandit', '-f', 'custom', '--msg-template', '{line}: {msg}', '-ll', '-i', file_path],
                                capture_output=True, text=True)
        return result.stdout

    def filter_bandit_results(self, bandit_results, added_line_numbers):
        """Filters Bandit results based on added line numbers."""
        relevant_results = []
        for line in bandit_results.split('\n'):
            parts = line.split(':')
            # Check if first part is a line number
            if len(parts) > 1 and parts[0].isdigit():
                line_number = int(parts[0])
                if line_number in added_line_numbers:
                    relevant_results.append(line)
        return relevant_results
