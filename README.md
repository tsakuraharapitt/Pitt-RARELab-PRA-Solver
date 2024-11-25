# RARE Lab PRA Solver (Beta)

## Overview
The RARE Lab PRA Solver quantifies a PRA model consisting of an event tree and fault trees. It provides detailed output in XML format.
If you find any issues with the program, please post them on the [ISSUES](https://github.com/tsakuraharapitt/Pitt-RARELab-PRA-Solver/issues) page. 

## Disclaimer
This software is a **preliminary beta version** and has not been verified or validated. This tool is provided for **educational purposes only**.
- **Do not** rely on this tool for real-world or safety-critical decision-making.  
- Use the results with caution, as the code may contain errors or limitations.

## Requirements
- **Python version**: 3.6 or later
- **Dependencies**:
  - `sympy` (for Boolean algebra operations)

## Installation
### 1. Clone the Repository
Use Git to clone the repository to your local machine:
```bash
git clone https://github.com/tsakuraharapitt/Pitt-RARELab-PRA-Solver.git
cd RARELab-PRA-Solver
```
Alternatively, you can download the repository as a ZIP file from GitHub and extract it.
### 2. Install Dependencies:
```
pip install -r requirements.txt
```
## Usage
### Run the Program:
```
python RARE-PRASolver-v0.1.py
```
### Provide Input: 
When running the program, the following prompt will be displayed. Then, enter the path/name of an XML input file (e.g., sample_input.xml):
```
Please enter the path to the XML input file: sample_input.xml
```
If the input file is located in the same directory, only the file name is required. The entire file path must be entered if the input file is placed in a different directory. 
### View Results:
Output data are stored in another XML file that will be created in the same directory.
```
Results are saved to sample_input_output.xml.
```
### Example Input
Here’s an example of an XML input file:
```
<PRAModel>
    <Scenarios>
        <Scenario name="S1" Outcome="major failure">IE*A</Scenario>
        <Scenario name="S2" Outcome="minor failure">IE*_A*B</Scenario>
        <Scenario name="S3" Outcome="minor failure">IE*_A*_B*C</Scenario>
        <Scenario name="S4" Outcome="success">IE*_A*_B*_C</Scenario>
    </Scenarios>
    <InitiatingEvent>
        <Probability>0.05</Probability>
    </InitiatingEvent>
    <TopEvents>
        <Event name="A">a*b + c*d</Event>
        <Event name="B">a*e + c*f</Event>
        <Event name="C">a*g</Event>
    </TopEvents>
    <Probabilities>
        <BasicEvent name="a">0.1</BasicEvent>
        <BasicEvent name="b">0.1</BasicEvent>
        <BasicEvent name="c">0.1</BasicEvent>
        <BasicEvent name="d">0.1</BasicEvent>
        <BasicEvent name="e">0.1</BasicEvent>
        <BasicEvent name="f">0.1</BasicEvent>
        <BasicEvent name="g">0.05</BasicEvent>
    </Probabilities>
</PRAModel>
```
Here, the underscore ("_") before each event represents a complement of each event. For instance, "_A" represents "not A" in Boolean logic. 
### Example Output
The program produces an XML output file, for example:
```
<Output>
  <Scenario name="S1" Outcome="major failure">
    <MinimalCutSets>(IE &amp; a &amp; b) | (IE &amp; c &amp; d)</MinimalCutSets>
    <Probability>9.950e-04</Probability>
  </Scenario>
  <Scenario name="S2" Outcome="minor failure">
    <MinimalCutSets>(IE &amp; a &amp; e &amp; ~b &amp; ~c) | (IE &amp; a &amp; e &amp; ~b &amp; ~d) | (IE &amp; c &amp; f &amp; ~a &amp; ~d) | (IE &amp; c &amp; f &amp; ~b &amp; ~d)</MinimalCutSets>
    <Probability>8.870e-04</Probability>
  </Scenario>
  <Scenario name="S3" Outcome="minor failure">
    <MinimalCutSets>(IE &amp; a &amp; g &amp; ~b &amp; ~c &amp; ~e) | (IE &amp; a &amp; g &amp; ~b &amp; ~d &amp; ~e &amp; ~f)</MinimalCutSets>
    <Probability>1.987e-04</Probability>
  </Scenario>
  <Scenario name="S4" Outcome="success">
    <MinimalCutSets>(IE &amp; ~a &amp; ~c) | (IE &amp; ~a &amp; ~d &amp; ~f) | (IE &amp; ~b &amp; ~c &amp; ~e &amp; ~g) | (IE &amp; ~b &amp; ~d &amp; ~e &amp; ~f &amp; ~g)</MinimalCutSets>
    <Probability>0.047919</Probability>
  </Scenario>
  <OutcomeTotals>
    <Outcome name="major failure">9.950e-04</Outcome>
    <Outcome name="minor failure">1.086e-03</Outcome>
    <Outcome name="success">0.047919</Outcome>
  </OutcomeTotals>
</Output>
```
## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
## Acknowledgment
This tool is being developed as part of an educational initiative at the University of Pittsburgh to advance risk analysis and reliability engineering. The goal is to equip the next generation of engineers with critical skills in risk and reliability assessment.
