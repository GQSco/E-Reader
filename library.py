import os

data_storage = "/sd/data/"

EPD_WIDTH = 250
EPD_HEIHGT = 122

class Book:
    def __init__(self, title, filename):
        self.title = title
        self.filename = filename
              
        self.pages = [0]
        self.total_pages = 0
        
        self.is_counted = False # track whether a book has pages tracked
        
        self.bookmark_filename = data_storage + self.title + ".bkm" # Loads current page in memory
        try:
            with open(self.bookmark_filename, 'r') as f:
                self.current_page = int(f.read().strip())
        except OSError:
            self.current_page = 0
            
    def get_title(self):
        return self.title
    
    def center_x(self, text):
        """Helper to center text based on standard 8-pixel wide characters."""
        text_width = len(text) * 8
        return int((EPD_WIDTH - text_width) / 2)
        
    def get_page(self):
        return self.current_page
    
    def ensure_counted(self, epd, txt_color, bkg_color):
        if self.is_counted == False:
            self.count_pages(epd, txt_color, bkg_color)
    
    def get_total_pages(self):
        return self.total_pages + 1
    
    def set_page(self, page):
        self.current_page = page
        
        with open(self.bookmark_filename, 'w') as f: # Stores current page in memory
            f.write(str(self.current_page))
    
    def loading_screen(self, epd, txt_color, bkg_color):
        epd.init()
        epd.fill(bkg_color)
        msg = "Calculating Pages..."
        epd.text(msg, self.center_x(msg), 52, txt_color)
        msg2 = "This might take a few minutes"
        epd.text(msg2, self.center_x(msg2), 70, txt_color)
        
        epd.display(epd.buffer)
        epd.sleep()
        
        
    def count_pages(self, epd, txt_color, bkg_color):
        
        cache_filename = data_storage + self.title + ".idx" # Stores page/character memory
        
        try:
            with open(cache_filename, 'r') as f:
                self.pages = [int(line.strip()) for line in f]
                self.total_pages = len(self.pages) - 1
                self.is_counted = True
                return
        except OSError:
            self.loading_screen(epd, txt_color, bkg_color)
        
        self.pages = [0] # Reset pages before counting (AI told me so)
        
        f = open(self.filename, 'r', encoding='utf-8')
        
        while True:
            f.seek(self.pages[-1])
            raw_text = f.read(500)
            
            if not raw_text:
                break # If the end of the book has been reached
            else:
                clean_text = self.format_text(raw_text)
                lines, chars_processed = self.wrap_text(clean_text)
                
                bytecount = len(raw_text[:chars_processed].encode('utf-8')) # Parse through raw text, display clean text               
                self.pages.append(self.pages[-1] + bytecount) # Add character indeces of new pages
        f.close()
        
        self.pages = self.pages[:-1] # Remove final index because there is no folllowing page
        self.total_pages = len(self.pages) - 1 # -1 for indexing
        
        # Save to cache file for future reference
        try:
            with open(cache_filename, 'w') as cache_file:
                for p in self.pages:
                    cache_file.write(str(p) + "\n")
                
                # Force pico to push data to the DS card
                cache_file.flush()
        except Exception as e:
            print("Could not save cache file:", e)
        
        self.is_counted = True
    
    def format_text(self, raw_text):
        clean_text = raw_text.replace('\r', ' ')
        clean_text = clean_text.replace('\f', ' ')
        
        clean_text = clean_text.replace("‘", "'").replace("’", "'")
        clean_text = clean_text.replace("“", '"').replace("”", '"')
        clean_text = clean_text.replace('©', 'C')
        clean_text = clean_text.replace('—', '-')
        clean_text = clean_text.replace("…", ",") # I mean, ok?
    
        return clean_text
    
    def wrap_text(self, txt):
        maxchar = 31
        maxlines = 14
        
        lines = []
        current_line = ""
        current_word = ""
        chars_processed = 0
        
        for char in txt:
            chars_processed += 1

            # Check for indentation
            if char == "\n":
                if len(lines) == 0 and current_line == "" and current_word == '': # If it's the first line and word
                    pass
                else:
                    current_line += current_word
                    current_word = ""
                    
                    # Create a new line
                    lines.append(current_line)
                    current_line = ""
                    
            elif char != " ":
                current_word += char
            else:
                current_line += current_word + " "
                current_word = ""
                
            # If the addition of another word would exceed the line character limit
            if len(current_line) + len(current_word) > maxchar:
                
                # Failsafe for if word is longer than 31 characters
                if current_line == "":
                    lines.append(current_word)
                    current_word = ""
                else:
                    lines.append(current_line.strip())
                    current_line = ""
                
            # If the number of lines span the whole page
            if len(lines) == maxlines:
                chars_processed -= len(current_word) # Current word will be on next page
                break
        
        # Capture the last frase
        if len(lines) < maxlines:
            current_line += current_word 
            lines.append(current_line)
        
        return lines, chars_processed
        
    def display_page(self, epd, txt_color, bkg_color):
        self.ensure_counted(epd, txt_color, bkg_color)
        
        f = open(self.filename, 'r', encoding='utf-8')
        
        # Go to first character of page x
        f.seek(self.pages[self.current_page])
        
        # Format text
        raw_text = f.read(500) # Read up to the max amount of characters per page
        clean_text = self.format_text(raw_text)
        lines, chars_processed = self.wrap_text(clean_text)
        
        # Write text to epaper and format page
        epd.init()
        epd.fill(bkg_color)

        epd.hline(0, 118, 250, txt_color)
        page_footer = f"Page {self.current_page + 1}/{self.total_pages + 1}"
        epd.text(page_footer, self.center_x(page_footer), 120, txt_color) # Center text
        
        for i in range(len(lines)):
            epd.text(lines[i], 2, 8*i + 6, txt_color)
        
        epd.Display_Base(epd.buffer)
        epd.sleep()

