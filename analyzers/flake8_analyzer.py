import subprocess


class Flake8Analyzer():

    def run_flake8_analysis(self, file_path, added_line_numbers):
        """Runs flake8 analysis and filters results based on added lines."""
        flake8_results = self.analyze_file_with_flake8(file_path)
        filtered_results = self.filter_flake8_results(
            flake8_results, added_line_numbers)

        if not filtered_results:
            print("\n\nFlake8: No issues found for the newly added or changed lines in '{}'.".format(
                file_path))
        else:
            print("\n\nFlake8: Filtered results for '{}':".format(file_path))
            for result in filtered_results:
                print(result)

    def analyze_file_with_flake8(self, file_path):
        """Executes flake8 static analysis and returns the result."""
        result = subprocess.run(
            ['flake8', file_path, '--format=%(row)d:%(text)s'], capture_output=True, text=True)
        return result.stdout

    def filter_flake8_results(self, flake8_results, added_line_numbers):
        """Filters flake8 results based on added line numbers."""
        relevant_results = []
        for line in flake8_results.split('\n'):
            if line:
                line_number = int(line.split(':')[0])
                if line_number in added_line_numbers:
                    relevant_results.append(line)
        return relevant_results
