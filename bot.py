import sys
import os
import re

class MXLangInterpreter:
    def __init__(self):
        self.variables = {}
        self.functions = {}
        self.output = []
        
    def runprint(self, message):
        """Main print function for MX language"""
        # Handle string concatenation
        if '+' in message:
            parts = message.split('+')
            result = ''
            for part in parts:
                part = part.strip().strip('"\'')
                if part in self.variables:
                    result += str(self.variables[part])
                else:
                    result += part
            print(result)
            self.output.append(result)
        else:
            # Handle variables
            message = message.strip().strip('"\'')
            if message in self.variables:
                print(self.variables[message])
                self.output.append(str(self.variables[message]))
            else:
                print(message)
                self.output.append(message)
    
    def let(self, var_name, value):
        """Variable declaration"""
        self.variables[var_name] = value
        
    def add(self, a, b):
        """Add function"""
        return a + b
    
    def sub(self, a, b):
        """Subtract function"""
        return a - b
    
    def mul(self, a, b):
        """Multiply function"""
        return a * b
    
    def div(self, a, b):
        """Divide function"""
        return a / b if b != 0 else 0
    
    def if_stmt(self, condition, true_block, false_block=None):
        """If statement"""
        if eval(condition, self.variables):
            self.execute_block(true_block)
        elif false_block:
            self.execute_block(false_block)
    
    def execute_block(self, lines):
        """Execute multiple lines of MX code"""
        for line in lines:
            self.parse_line(line)
    
    def parse_line(self, line):
        """Parse and execute a single line of MX code"""
        line = line.strip()
        
        if not line or line.startswith('//') or line.startswith('#'):
            return
            
        # runprint command
        if line.startswith('runprint'):
            match = re.match(r'runprint\((.*)\)', line)
            if match:
                self.runprint(match.group(1))
        
        # let command
        elif line.startswith('let'):
            match = re.match(r'let\s+(\w+)\s*=\s*(.+)', line)
            if match:
                var_name = match.group(1)
                value = match.group(2).strip()
                # Check if value is number
                if value.isdigit():
                    value = int(value)
                elif value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value in self.variables:
                    value = self.variables[value]
                self.let(var_name, value)
        
        # Mathematical operations
        elif line.startswith('calc'):
            match = re.match(r'calc\s+(\w+)\s*=\s*(.+)', line)
            if match:
                var_name = match.group(1)
                expression = match.group(2)
                try:
                    result = eval(expression, self.variables)
                    self.let(var_name, result)
                except:
                    pass
    
    def execute_file(self, filename):
        """Execute MX file"""
        try:
            with open(filename, 'r') as file:
                lines = file.readlines()
                for line in lines:
                    self.parse_line(line)
            return True, "Execution successful"
        except Exception as e:
            return False, f"Error: {str(e)}"
