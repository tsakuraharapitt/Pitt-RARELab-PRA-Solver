"""
RARE PRA Solver (Beta)

Disclaimer:
This code is a preliminary beta version and has not been verified or validated.
It is provided for educational purposes only. Do not use this code to support
decision-making in real-world or safety-critical applications. 

Author: Tatsuya Sakurahara
Version: 0.1 (Beta)
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from sympy import symbols, Not, Or, And, simplify_logic, to_dnf
from itertools import combinations
import os
from collections import defaultdict
import re

def print_disclaimer():
    """Print a disclaimer about the tool's limitations."""
    disclaimer = """
    ========================================================
    RARE Lab PRA Solver (Beta)

    DISCLAIMER:
    This tool is a preliminary beta version and is provided 
    for educational purposes only. It has not undergone formal 
    verification or validation. 

    DO NOT rely on this tool for decision-making in real-world 
    or safety-critical applications.
    
    Author: RARE Lab at Pitt
    Version: 0.1 (Beta)
    Release Date: 11/25/2024
    ========================================================
    """
    print(disclaimer)

def parse_xml(file_path):
    """Parse the XML file and extract PRA model information."""
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    # Get the list of scenarios
    scenarios = []
    for scenario in root.find('Scenarios'):
        name = scenario.attrib['name']
        outcome = scenario.attrib['Outcome']
        logic = scenario.text.strip()
        scenarios.append((name, outcome, logic))
    
    # Get the initiating event probability
    ie_probability = float(root.find('InitiatingEvent/Probability').text.strip())
    
    # Get top event Boolean expressions
    top_events = {}
    for event in root.find('TopEvents'):
        name = event.attrib['name']
        logic = event.text.strip()
        top_events[name] = logic
    
    # Get basic event probabilities, including IE
    probabilities = {"IE": ie_probability}  # Start with IE
    for prob in root.find('Probabilities'):
        name = prob.attrib['name']
        value = float(prob.text.strip())
        probabilities[name] = value
    
    return scenarios, top_events, probabilities

def create_boolean_expression(logic, symbols_dict):
    """Convert a string logic expression to a SymPy Boolean expression."""
    # Tokenize the string into components: complements, variables, operators, and parentheses
    tokens = re.split(r'(\W)', logic)  # Split by non-word characters while preserving operators

    # Translate the tokens into SymPy format
    translated_tokens = []
    for token in tokens:
        token = token.strip()
        if not token:  # Ignore empty tokens
            continue
        
        # Handle complement with "NOT_" prefix (e.g., "NOT_HPI" -> "Not(HPI)")
        if token.startswith("NOT_"):
            event_name = token[4:]
            if event_name in symbols_dict:
                translated_tokens.append(f"Not({symbols_dict[event_name]})")
            else:
                raise KeyError(f"Complement event '{event_name}' not found in symbols dictionary.")

        # Handle regular event (e.g., "HPI")
        elif token.isalnum():
            if token in symbols_dict:
                translated_tokens.append(f"{symbols_dict[token]}")
            else:
                raise KeyError(f"Event '{token}' not found in symbols dictionary.")

        # Handle operators (* for AND, + for OR)
        elif token == "*":
            translated_tokens.append("&")
        elif token == "+":
            translated_tokens.append("|")

        # Handle parentheses
        elif token == "(" or token == ")":
            translated_tokens.append(token)

        # Handle other unexpected symbols
        else:
            raise ValueError(f"Unexpected token '{token}' in logic expression.")

    # Join the translated tokens into a valid SymPy expression
    translated_logic = " ".join(translated_tokens)

    # Evaluate the expression using SymPy's And, Or, and Not operators
    return eval(translated_logic, {"And": And, "Or": Or, "Not": Not, **symbols_dict})


def compute_probability(expression, probabilities):
    """Compute the probability of a given Boolean expression involving minimal cut sets."""

    if expression.is_Atom:  # Base case: single event, return its probability
        event_name = str(expression)
        if event_name in probabilities:
            return probabilities[event_name]
        else:
            raise KeyError(f"Event '{event_name}' not found in probabilities dictionary.")
    
    if expression.func == And:  # Handle conjunctions (AND)
        p = 1.0
        for term in expression.args:
            p *= compute_probability(term, probabilities)
        return p

    elif expression.func == Or:  # Handle disjunctions (OR)
        # Use inclusion-exclusion principle for OR probability calculation
        total_probability = 0.0
        terms = list(expression.args)
        n = len(terms)
        
        # Apply the inclusion-exclusion principle for the disjunction of events
        for r in range(1, n + 1):
            for subset in combinations(terms, r):
                subset_intersection = And(*subset)
                subset_prob = compute_probability(subset_intersection, probabilities)
                if r % 2 == 1:  # Add for odd-sized subsets
                    total_probability += subset_prob
                else:  # Subtract for even-sized subsets
                    total_probability -= subset_prob
        return total_probability

    elif isinstance(expression, Not):  # Handle complement (NOT)
        event_name = str(expression.args[0])
        return 1 - compute_probability(expression.args[0], probabilities)

    else:
        raise ValueError(f"Unexpected expression type: {expression}")


def compute_union_probability(minimal_cut_sets, probabilities):
    """Calculate the exact probability using inclusion-exclusion principle."""
    total_probability = 0.0
    minimal_cut_set_list = minimal_cut_sets.args if minimal_cut_sets.func == Or else [minimal_cut_sets]

    # Apply inclusion-exclusion principle
    for r in range(1, len(minimal_cut_set_list) + 1):
        for subset in combinations(minimal_cut_set_list, r):
            # Simplify the intersection of the subset
            intersection = simplify_logic(And(*subset))
            if intersection == False:  # Skip null intersections
                continue
            intersection_probability = compute_probability(intersection, probabilities)
            if r % 2 == 1:  # Add for odd-sized subsets
                total_probability += intersection_probability
            else:  # Subtract for even-sized subsets
                total_probability -= intersection_probability

    return total_probability

def format_probability(value):
    """Format the probability as scientific notation if abs(value) < 0.01, otherwise as a float."""
    if abs(value) < 0.01:
        return f"{value:.3e}"  # Scientific notation
    else:
        return f"{value:.6f}"  # Standard float notation

def save_results_to_xml(input_file, results, outcome_totals):
    """Save the results to an XML output file."""
    # Create the root element
    root = ET.Element("Output")
    
    # Add results for each scenario
    for name, outcome, minimal_cut_sets, exact_probability in results:
        scenario_elem = ET.SubElement(root, "Scenario", name=name, Outcome=outcome)
        ET.SubElement(scenario_elem, "MinimalCutSets").text = str(minimal_cut_sets)
        ET.SubElement(scenario_elem, "Probability").text = format_probability(exact_probability)
    
    # Add outcome totals
    totals_elem = ET.SubElement(root, "OutcomeTotals")
    for outcome, total_prob in outcome_totals.items():
        ET.SubElement(totals_elem, "Outcome", name=outcome).text = format_probability(total_prob)
    
    # Convert the tree to a pretty XML string
    xml_string = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    
    # Define output file name
    output_file = f"{os.path.splitext(input_file)[0]}_output.xml"
    
    # Write to file
    with open(output_file, "w") as f:
        f.write(xml_string)
    
    print(f"Results saved to: {output_file}")

def fully_reduce_cut_sets(expression):
    """
    Fully reduce the Boolean expression to ensure minimal cut sets.
    Convert the expression to Disjunctive Normal Form (DNF) and simplify.
    """
    # Convert to Disjunctive Normal Form (DNF), allowing it for larger expressions
    dnf_expression = to_dnf(expression, simplify=True, force=True)

    # Use simplify_logic to further reduce the expression
    minimized_expression = simplify_logic(dnf_expression, form='dnf')

    return minimized_expression

def main():
    # Prompt user for the input file path
    file_path = input("Please enter the path to the XML input file: ").strip()
    
    try:
        # Parse the XML file
        scenarios, top_events, probabilities = parse_xml(file_path)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return
    except ET.ParseError as e:
        print(f"Error parsing XML file: {e}")
        return
    
    # Create Sympy symbols for basic events and top events
    basic_events = {name: symbols(name) for name in probabilities.keys()}
    top_event_symbols = {name: symbols(name) for name in top_events.keys()}
    
    # Create Boolean expressions for top events
    top_event_expressions = {name: create_boolean_expression(logic, {**basic_events, **top_event_symbols}) for name, logic in top_events.items()}
    
    # Compute probabilities for each scenario
    results = []
    outcome_totals = defaultdict(float)
    for name, outcome, logic in scenarios:
        # Parse the scenario of interest
        scenario_expression = create_boolean_expression(logic, {**basic_events, **top_event_symbols, **top_event_expressions})
        
        # Simplify to minimal cut sets using DNF and further reduction
        minimal_cut_sets = simplify_logic(scenario_expression, form='dnf')
        fully_reduced_cut_sets = fully_reduce_cut_sets(minimal_cut_sets)
        
        # Compute the probability
        exact_probability = compute_union_probability(fully_reduced_cut_sets, probabilities)
        
        # Store the results
        results.append((name, outcome, fully_reduced_cut_sets, exact_probability))
        outcome_totals[outcome] += exact_probability
    
    # Save results to an XML file
    save_results_to_xml(file_path, results, outcome_totals)

if __name__ == "__main__":
    main()
