import cgi
import logging
import re
import os

class CyclicTokenDefinitionException (Exception):
    """
    Exception stating that there is a cycle in the token definition.
    e.g:    FOO = @@@BAR@@@
            BAR = @@@FOO@@@
    """
    def __init__ (self, variables):
        self.variables = variables

    def __str__ (self):
        return "There is a cycle in the token definitions: %s" % (str(self.variables))

class MissingTokenException (Exception):
    """
    Exception stating that a value for a given token 
    has not been found in the token definition. 
    """
    
    def __init__ (self, token, file=None):
        self.token = token
        self.file = file

    def __str__ (self):
        msg = "Missing token '%s'" % self.token
        if self.file:
            msg += " in file '%s'" % self.file
        return msg

class TokenReplacer (object):
    """
    Class that replaces tokens in strings. 
    
    The general syntax is
        @@@TOKEN@@@
    """

    TOKEN_PATTERN = re.compile(r"@@@([A-Za-z0-9_-]*)@@@")

    @classmethod
    def filter_directory (cls, 
                          directory, 
                          variables_definition_directory, 
                          replacer_function=None, html_escape=False, html_escape_function=None):
        logging.info("Filtering files in %s", directory)
        
        token_replacer = cls.from_directory(os.path.abspath(variables_definition_directory), 
                                            replacer_function=replacer_function, html_escape_function=html_escape_function)
        
        for root, _, filenames in os.walk(directory):
            if variables_definition_directory in root:
                continue
            for filename in filenames:
                absolute_filename = os.path.join(root, filename)
                logging.debug("Filtering file %s", absolute_filename)
                token_replacer.filter_file(absolute_filename, html_escape=html_escape)

    @classmethod
    def from_directory (cls, directory, replacer_function=None, html_escape_function=None):
        logging.debug("Initializing token replacer of class %s from directory %s",
                      cls.__name__, directory)

        token_values = {}
        absolute_path = os.path.abspath(directory)
        
        for name in os.listdir(absolute_path):
            candidate = os.path.join(absolute_path, name)
            if os.path.isfile(candidate):
                with open(candidate) as property_file:
                    token_values[name] = property_file.read().strip()
        
        return cls(token_values=token_values, replacer_function=replacer_function, html_escape_function=html_escape_function)

    def __init__ (self, token_values={}, replacer_function=None, html_escape_function=None):
        self.token_values = {}
        for token in token_values:
            self.token_values[token] = token_values[token].strip()
        
        if not replacer_function:
            def replacer_function (token, replacement):
                __pychecker__ = 'unusednames=token'
                return replacement
        else:
            logging.debug("Using custom replacer_function %s", 
                          replacer_function.__name__)

        if not html_escape_function:
            def html_escape_function(filename, content):
                content = cgi.escape(content, quote=True)
                return "<!DOCTYPE html><html><head><title>%s</title></head><body><pre>%s</pre></body></html>" % (filename, content)


        self.replacer_function = replacer_function
        self.html_escape_function = html_escape_function

        self.token_values = self._replace_tokens_in_token_values(self.token_values)
        

    def filter (self, content):
        while True:
            match = TokenReplacer.TOKEN_PATTERN.search(content)
            if not match:
                return content
            token_name = match.group(1)
            if not token_name in self.token_values:
                raise MissingTokenException(token_name)
            replacement = self.replacer_function(token_name, 
                                                 self.token_values[token_name])
            
            content = content.replace("@@@%s@@@" % token_name, replacement)

    def filter_file (self, filename, html_escape=False):
        __pychecker__ = "missingattrs=token"
        try:
            with open(filename, "r") as input_file:
                file_content = input_file.read()

            if html_escape:
                file_content = self.html_escape_function(os.path.basename(filename), file_content)

            file_content_filtered = self.filter(file_content)
            
            with open(filename, "w") as output_file:
                output_file.write(file_content_filtered)
        except MissingTokenException as exception:
            raise MissingTokenException(exception.token, filename)

    def _replace_tokens_in_token_values(self, token_values):
        valid_tokens = dict((key, value) for (key, value) in token_values.iteritems() if not TokenReplacer.TOKEN_PATTERN.search(value))
        invalid_tokens = dict((key, value) for (key, value) in token_values.iteritems() if TokenReplacer.TOKEN_PATTERN.search(value))

        while invalid_tokens:
            still_invalid_tokens = {}
            replace_count = 0
            for (key, value) in invalid_tokens.iteritems():
                token_names = TokenReplacer.TOKEN_PATTERN.findall(value)
                for token_name in token_names:
                    if token_name in valid_tokens:
                        value = value.replace("@@@%s@@@" % token_name, valid_tokens[token_name])
                        replace_count += 1

                if TokenReplacer.TOKEN_PATTERN.search(value):
                    still_invalid_tokens[key] = value
                else:
                    valid_tokens[key] = value

            # there are still invalid tokens and we could not replace any of them in the last loop cycle, so let's throw an error
            if still_invalid_tokens and not replace_count:
                raise CyclicTokenDefinitionException(still_invalid_tokens)

            invalid_tokens = still_invalid_tokens

        return valid_tokens