from .log_parser import LogParser
from .puml_generator import PUMLGenerator


def tracelog_to_puml(log_file="trace.log", output_puml_file="trace_diagram.puml"):
    log_file = log_file
    output_puml_file = output_puml_file

    # Parse the log file
    parser = LogParser(log_file)
    parser.parse()

    # Generate PUML
    generator = PUMLGenerator(output_puml_file)
    generator.write_puml(parser.interactions, parser.functions)
