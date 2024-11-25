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
from sympy import symbols, Not, simplify_logic, And, Or
from itertools import combinations
import os
from collections import defaultdict

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
    Release Date: 11/30/2024
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
    """Convert a string logic expression to a Sympy Boolean expression."""
    # Replace underscores (_) with Not notation for complements
    for event in symbols_dict.keys():
        logic = logic.replace(f"_{event}", f"Not({event})")
    # Replace operators with Sympy syntax
    logic = logic.replace("*", " & ").replace("+", " | ")
    return eval(logic, {**symbols_dict, "And": And, "Or": Or, "Not": Not})

def compute_probability(cut_set, probabilities):
    """Compute the probability of a single minimal cut set."""
    p = 1.0
    if cut_set.func == And:  # Handle conjunctions (AND)
        for term in cut_set.args:
            if isinstance(term, Not):  # Handle complement events
                p *= 1 - probabilities[str(term.args[0])]
            else:
                p *= probabilities[str(term)]
    elif cut_set.func == Not:  # Handle single NOT event
        p = 1 - probabilities[str(cut_set.args[0])]
    else:  # Handle single event
        p = probabilities[str(cut_set)]
    return p

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

def main():
    
    # Print disclaimer
    print_disclaimer()

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
    top_event_expressions = {name: create_boolean_expression(logic, basic_events) for name, logic in top_events.items()}
    
    # Compute probabilities for each scenario
    results = []
    outcome_totals = defaultdict(float)
    for name, outcome, logic in scenarios:
        # Parse the scenario of interest
        scenario_expression = create_boolean_expression(logic, {**basic_events, **top_event_symbols, **top_event_expressions})
        
        # Simplify to minimal cut sets
        minimal_cut_sets = simplify_logic(scenario_expression, form='dnf')
        
        # Compute the probability
        exact_probability = compute_union_probability(minimal_cut_sets, probabilities)
        
        # Store the results
        results.append((name, outcome, minimal_cut_sets, exact_probability))
        outcome_totals[outcome] += exact_probability
    
    # Save results to an XML file
    save_results_to_xml(file_path, results, outcome_totals)

if __name__ == "__main__":
    main()
