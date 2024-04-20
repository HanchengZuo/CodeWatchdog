import subprocess


class PylintAnalyzer():

    def run_pylint_analysis(self, file_path, added_line_numbers):
        """Runs pylint analysis and filters results based on added lines."""
        pylint_results = self.analyze_file_with_pylint(file_path)
        filtered_results = self.filter_pylint_results(
            pylint_results, added_line_numbers)
        print("Filtered pylint results:")
        for result in filtered_results:
            print(result)

    def analyze_file_with_pylint(self, file_path):
        """Executes pylint static analysis and returns the result."""
        result = subprocess.run(['pylint', file_path, '--output-format=text', '--msg-template="{line}:{msg}"'],
                                capture_output=True, text=True)
        return result.stdout

    def filter_pylint_results(self, pylint_results, added_line_numbers):
        """Filters pylint results based on added line numbers."""
        relevant_results = []
        for line in pylint_results.split('\n'):
            parts = line.split(':')
            # Ensure that the first part is a number
            if len(parts) > 1 and parts[0].isdigit():
                line_number = int(parts[0])
                if line_number in added_line_numbers:
                    relevant_results.append(line)
        return relevant_results
