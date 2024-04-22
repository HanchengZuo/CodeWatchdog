import subprocess


class BanditAnalyzer:

    def run_bandit_analysis(self, file_path, added_line_numbers):
        """Runs Bandit analysis and filters results based on added lines."""
        bandit_results = self.analyze_file_with_bandit(file_path)
        filtered_results = self.filter_bandit_results(
            bandit_results, added_line_numbers)

        if not filtered_results:
            print("\nBandit: No issues found for the newly added or changed lines in '{}'.".format(
                file_path))
        else:
            print("\nBandit: Filtered results for '{}':".format(file_path))
            for result in filtered_results:
                print(result)

    def analyze_file_with_bandit(self, file_path):
        """Executes Bandit security analysis and returns the result."""
        msg_template = "{path}:{line}: {test_id}[{severity}][{confidence}]: {msg}"
        result = subprocess.run(
            ['bandit', '-r', '-f', 'custom', '--msg-template',
                msg_template, '-ll', '-i', file_path],
            capture_output=True, text=True
        )
        return result.stdout

    def filter_bandit_results(self, bandit_results, added_line_numbers):
        """Filters Bandit results based on added line numbers."""
        relevant_results = []
        for line in bandit_results.split('\n'):
            if line.strip() and ':' in line:
                parts = line.split(':', 2)  # Split on the first two ':' only
                if len(parts) > 2 and parts[1].isdigit():
                    line_number = int(parts[1])
                    if line_number in added_line_numbers:
                        relevant_results.append(line)
        return relevant_results
