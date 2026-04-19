import sys
import os
import re

class MXLangInterpreter:
    def __init__(self):
        self.variables = {}
        self.functions = {}
        self.output = []
        
    def runprint(self, message):
        """Main print function for MX language - FIXED VERSION"""
        try:
            # Check if message contains + for concatenation
            if '+' in message:
                parts = message.split('+')
                result = ''
                for part in parts:
                    part = part.strip()
                    # Remove quotes if present (string literal)
                    if (part.startswith('"') and part.endswith('"')) or (part.startswith("'") and part.endswith("'")):
                        part = part[1:-1]
                        result += part
                    else:
                        # This is a variable name - look it up in variables dictionary
                        if part in self.variables:
                            result += str(self.variables[part])
                        else:
                            # If not a variable, treat as string
                            result += part
                print(result)
                self.output.append(result)
                return result
            else:
                # No concatenation - single value
                message = message.strip()
                # Check if it's a string literal
                if (message.startswith('"') and message.endswith('"')) or (message.startswith("'") and message.endswith("'")):
                    message = message[1:-1]
                    print(message)
                    self.output.append(message)
                    return message
                # Check if it's a variable
                elif message in self.variables:
                    print(self.variables[message])
                    self.output.append(str(self.variables[message]))
                    return str(self.variables[message])
                # Default - print as is
                else:
                    print(message)
                    self.output.append(message)
                    return message
        except Exception as e:
            error_msg = f"Runprint error: {str(e)}"
            print(error_msg)
            self.output.append(error_msg)
            return error_msg
    
    def let(self, var_name, value):
        """Variable declaration"""
        try:
            # Try to convert value to number if possible
            if isinstance(value, str):
                if value.isdigit():
                    value = int(value)
                elif value.replace('.', '', 1).isdigit() and value.count('.') <= 1:
                    value = float(value)
            
            self.variables[var_name] = value
            return True
        except Exception as e:
            print(f"Error in let: {str(e)}")
            return False
    
    def parse_line(self, line):
        """Parse and execute a single line of MX code"""
        line = line.strip()
        
        if not line or line.startswith('//') or line.startswith('#'):
            return
        
        # Handle runprint command
        if line.startswith('runprint'):
            # Extract content between parentheses
            match = re.match(r'runprint\((.*)\)', line)
            if match:
                self.runprint(match.group(1))
            return
        
        # Handle let command
        if line.startswith('let'):
            # Parse: let variable = value
            match = re.match(r'let\s+(\w+)\s*=\s*(.+)', line)
            if match:
                var_name = match.group(1)
                value = match.group(2).strip()
                
                # Check if value is a calculation
                if '+' in value and not (value.startswith('"') or value.startswith("'")):
                    # Handle addition of variables
                    parts = value.split('+')
                    total = 0
                    is_string_concat = False
                    
                    for part in parts:
                        part = part.strip()
                        if part in self.variables:
                            if isinstance(self.variables[part], (int, float)):
                                total += self.variables[part]
                            else:
                                is_string_concat = True
                        else:
                            try:
                                total += float(part)
                            except:
                                is_string_concat = True
                    
                    if is_string_concat:
                        # Handle string concatenation
                        result = ''
                        for part in parts:
                            part = part.strip()
                            if part in self.variables:
                                result += str(self.variables[part])
                            else:
                                result += part
                        self.let(var_name, result)
                    else:
                        self.let(var_name, total)
                elif value in self.variables:
                    self.let(var_name, self.variables[value])
                else:
                    self.let(var_name, value)
            return
    
    def execute_file(self, filename):
        """Execute MX file"""
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                for line in lines:
                    self.parse_line(line)
            return True, "Execution successful"
        except FileNotFoundError:
            return False, f"File '{filename}' not found"
        except Exception as e:
            return False, f"Error: {str(e)}"

def main():
    """Main function to run MX interpreter from command line"""
    if len(sys.argv) < 2:
        print("Usage: python mx_interpreter.py <filename.mx>")
        sys.exit(1)
    
    filename = sys.argv[1]
    
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' not found!")
        sys.exit(1)
    
    # Create MX interpreter instance
    mx = MXLangInterpreter()
    
    # Execute MX file
    print(f"\n{'='*50}")
    print(f"Executing MX Language File: {filename}")
    print(f"{'='*50}\n")
    
    success, message = mx.execute_file(filename)
    
    print(f"\n{'='*50}")
    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    main()
