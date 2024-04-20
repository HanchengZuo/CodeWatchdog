import subprocess


class MypyAnalyzer():

    def run_mypy_analysis(self, file_path, added_line_numbers):
        """Runs mypy type checking and filters results based on added lines."""
        mypy_results = self.analyze_file_with_mypy(file_path)
        filtered_results = self.filter_mypy_results(
            mypy_results, added_line_numbers)
        print("Filtered mypy results:")
        for result in filtered_results:
            print(result)

    def analyze_file_with_mypy(self, file_path):
        """Executes mypy static type checking and returns the result."""
        result = subprocess.run(['mypy', file_path, '--no-color-output',
                                '--hide-error-context'], capture_output=True, text=True)
        return result.stdout

    def filter_mypy_results(self, mypy_results, added_line_numbers):
        """Filters mypy results based on added line numbers."""
        relevant_results = []
        for line in mypy_results.split('\n'):
            parts = line.split(':')
            # Assumes format: filename:line_number:message
            if len(parts) > 2 and parts[1].isdigit():
                line_number = int(parts[1])
                if line_number in added_line_numbers:
                    relevant_results.append(line)
        return relevant_results
