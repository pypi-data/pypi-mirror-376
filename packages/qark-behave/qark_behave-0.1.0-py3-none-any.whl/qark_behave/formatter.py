"""QArk Formatter for Behave"""

import os
from allure_behave.formatter import AllureFormatter


class QArkFormatter(AllureFormatter):
    """QArk Behave formatter.
    
    This formatter generates test results in a specified directory (default: qark-results).
    """
    
    name = "qark"
    description = "QArk formatter for Behave test results"
    
    def __init__(self, stream_opener, config):
        """Initialize the QArk formatter.
        
        Args:
            stream_opener: Stream opener for output
            config: Behave configuration object
        """
        # Set default output directory if not specified
        if not hasattr(config, 'output') or not config.output:
            config.output = ["qark-results"]
        elif isinstance(config.output, list) and len(config.output) == 0:
            config.output = ["qark-results"]
        
        # Ensure output directory exists
        output_dir = config.output[0] if isinstance(config.output, list) else config.output
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        super().__init__(stream_opener, config)
        
        self._original_stream = self.stream
        self.stream = self._create_filtered_stream()
    
    def _create_filtered_stream(self):
        class FilteredStream:
            def __init__(self, original_stream):
                self.original_stream = original_stream
            
            def write(self, text):
                filtered_text = text.replace("Allure", "QArk")
                filtered_text = filtered_text.replace("allure", "qark")
                return self.original_stream.write(filtered_text)
            
            def flush(self):
                return self.original_stream.flush()
            
            def __getattr__(self, name):
                return getattr(self.original_stream, name)
        
        return FilteredStream(self._original_stream)
    
    def feature(self, feature):
        """Process feature start."""
        super().feature(feature)
    
    def scenario(self, scenario):
        """Process scenario start."""
        super().scenario(scenario)
    
    def step(self, step):
        """Process step execution."""
        super().step(step)
    
    def close(self):
        """Close the formatter and finalize output."""
        super().close()
        
        # Print completion message
        output_dir = self.config.output[0] if isinstance(self.config.output, list) else self.config.output
        print(f"\nQArk test results generated in: {output_dir}")