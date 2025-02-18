import tkinter as tk
from tkinter import ttk, messagebox
import csv
import barcode # type: ignore
from barcode.writer import ImageWriter # type: ignore
from reportlab.pdfgen import canvas
from tkinter import filedialog
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


class InventorySystem:
    def __init__(self, root):
        self.root = root
        self.root.title("מערכת ניהול מלאי")
        self.root.geometry("1200x600")
        
        # משתנים
        self.categories = ["מחשבים ניידים", "מחשבים נייחים", "AIO", "מסכים"]
        self.current_category = tk.StringVar(value=self.categories[0])
        self.product_counter = 1
        self.archived_items = []
        self.category_data = {cat: [] for cat in self.categories}
        
        self.create_widgets()
        self.load_archive()
        self.load_data()
        
        # print("archive", self.archived_items)
        # print("current", self.category_data)
        
    def create_widgets(self):
        # חיפוש
        search_frame = tk.Frame(self.root)
        search_frame.pack(pady=5, fill=tk.X, padx=10)
        tk.Label(search_frame, text="חיפוש:").pack(side=tk.RIGHT, padx=5)
        self.search_entry = tk.Entry(search_frame)
        self.search_entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        self.search_entry.bind('<KeyRelease>', self.search_products)
        
        # יצירת כפתורי קטגוריות
        category_frame = tk.Frame(self.root)
        category_frame.pack(pady=5)
        
        for cat in self.categories:
            tk.Button(category_frame, text=cat, 
                     command=lambda c=cat: self.change_category(c)).pack(side=tk.RIGHT, padx=5)
        
        # תצוגת סכום כולל
        self.total_label = tk.Label(category_frame, text="סה\"כ: 0 ₪", font=("Arial", 12, "bold"))
        self.total_label.pack(side=tk.LEFT, padx=20)
        
        # יצירת טבלה
        columns = ("מספר", "ספק", "מספר סידורי", "מותג", "דגם", "מסך", "מעבד", "זיכרון", 
                  "דיסק", "כרטיס מסך", "רזולוציה", "מגע", "מערכת הפעלה", "סטטוס", "מחיר", "ברקוד")
        
        table_frame = tk.Frame(self.root)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=8)
        
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # הוספת מיון בלחיצה על כותרות העמודות
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_column(c))
            self.tree.column(col, width=100, anchor=tk.CENTER)
            

        
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)
        
        # הוספת אירוע לחיצה כפולה לעריכה
        self.tree.bind('<Double-1>', self.edit_item)
        
        # יצירת טופס הזנה
        input_frame = tk.Frame(self.root)
        input_frame.pack(pady=5)
        
        self.entries = []
        fields = ["מספר", "ספק", "מספר סידורי", "מותג", "דגם", "מסך", "מעבד", "זיכרון", 
                 "דיסק", "כרטיס מסך", "רזולוציה", "מגע", "מערכת הפעלה", "סטטוס", "מחיר"]
        
        row1 = tk.Frame(input_frame)
        row1.pack()
        row2 = tk.Frame(input_frame)
        row2.pack()
        
        for i, field in enumerate(fields):
            container = row1 if i < 7 else row2
            frame = tk.Frame(container)
            frame.pack(side=tk.RIGHT, padx=5, pady=5)
            
            tk.Label(frame, text=field).pack()
            entry = tk.Entry(frame, width=12)
            if field == "מספר":
                entry.config(state='readonly', background='#f0f0f0')
                entry.insert(0, str(self.product_counter))  # Auto-populate initial value
            entry.pack()
            self.entries.append(entry)
        
        # כפתורי פעולות
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Add הוסף מוצר", command=self.add_product).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="Delete מחק מוצר", command=self.delete_product).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="Print הדפס מדבקה", command=self.print_label).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="Archive ארכיון", command=self.show_archive).pack(side=tk.RIGHT, padx=5)

    def generate_barcode(self, values):
        """Generate a valid EAN-13 barcode."""
        try:
            serial_number = str(values[1])  # Convert to string to prevent iteration errors

            barcode_text = ''.join(filter(str.isdigit, serial_number))  # Keep only digits
            
            barcode_text = barcode_text[:12].ljust(12, '0')  # Pad with zeroes if needed

            return barcode_text
        except Exception as e:
            messagebox.showerror("שגיאה", f"שגיאה ביצירת ברקוד: {str(e)}")
            return "000000000000"
    
        """Generate a valid EAN-13 barcode."""
        try:
            # Extract only numbers from serial number
            barcode_text = ''.join(filter(str.isdigit, values[1]))  # Keep only digits from serial number
            
            # Ensure length of 12 digits (EAN-13 requires 12 + 1 checksum digit)
            barcode_text = barcode_text[:12].ljust(12, '0')  # Pad with zeroes if needed

            return barcode_text
        except Exception as e:
            messagebox.showerror("שגיאה", f"שגיאה ביצירת ברקוד: {str(e)}")
            return "000000000000"
    
        """יצירת ברקוד מנתוני המוצר"""
        try:
            # יצירת מחרוזת ייחודית מהמספר הסידורי ושם המוצר
            barcode_text = f"{values[1]}{values[2][:2]}{values[3][:2]}".upper()
            barcode_text = ''.join(filter(str.isalnum, barcode_text))
            barcode_text = barcode_text[:12].ljust(12, '0')
            return barcode_text
        except Exception as e:
            messagebox.showerror("שגיאה", f"שגיאה ביצירת ברקוד: {str(e)}")
            return "000000000000"

    def sort_column(self, col):
        """מיון הטבלה לפי עמודה"""
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        try:
            # ניסיון למיין כמספרים
            l.sort(key=lambda t: float(t[0]))
        except ValueError:
            # אם לא מצליח, ממיין כטקסט
            l.sort()
        
        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)
    
    def edit_item(self, event):
        """עריכת פריט בלחיצה כפולה"""
        selected = self.tree.selection()
        if not selected:
            return
            
        item = self.tree.item(selected[0])['values']
        # מילוי הטופס בערכים הקיימים
        # for entry, value in zip(self.entries, item):
        #     entry.delete(0, tk.END)
        #     entry.insert(0, str(value))
            
        for index, (entry, value) in enumerate(zip(self.entries, item)):
            entry.config(state='normal')  # Temporarily set to normal to insert value
            entry.delete(0, tk.END)
            entry.insert(0, str(value))
            
            # If the field is "ספק", set it back to read-only after inserting the value
            if index == 0:
                entry.config(state='readonly', background='#f0f0f0')
        # מחיקת הפריט הישן
        self.tree.delete(selected)
    def total_items_in_categories(self):
        total = 0
        for category, items in self.category_data.items():
            total += len(items)  # Count the number of *lists* in each category
            print(f"Total items in category '{category}': {len(items)}")  # Print individual category counts

        return total

    def add_product(self):
        values = [e.get() for e in self.entries]
        if not values[1].strip():  # Assuming 'מספר' is at index 1
            messagebox.showwarning("שגיאה", "נא למלא את שדה מספר")
            if any(not v.strip() for v in values):
                messagebox.showwarning("שגיאה", "נא למלא את כל השדות")
            return
            
        # הוספת ברקוד לערכים
        barcode_value = self.generate_barcode(values)
        values.append(barcode_value)
        
        values[0] = self.total_items_in_categories() + 1
        self.tree.insert('', tk.END, values=values)
        self.category_data[self.current_category.get()].append(values[1:])
        
        # ניקוי שדות
        for entry in self.entries[1:]:
            entry.delete(0, tk.END)
            
        self.update_total()
        self.save_data()

    def delete_product(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("שגיאה", "נא לבחור מוצר למחיקה")
            return
        item = self.tree.item(selected[0])['values']
        barcode_value = self.generate_barcode(item)
        item[15] = barcode_value
        self.archived_items.append(item[1:])
        self.save_archive()
        
        # הסרה מהקטגוריה הנוכחית
        self.category_data[self.current_category.get()] = [
            x for x in self.category_data[self.current_category.get()]
            if x != item[1:]
        ]
        
        self.tree.delete(selected)
        self.update_total()
        self.save_data()

    def show_archive(self):
        archive_window = tk.Toplevel(self.root)
        archive_window.title("ארכיון מוצרים")
        archive_window.geometry("1000x500")
        
        columns = ["מספר", "מספר סידורי", "מותג", "דגם", "מסך", "מעבד", "זיכרון", 
                 "דיסק", "כרטיס מסך", "רזולוציה", "מגע", "מערכת הפעלה", "סטטוס", "מחיר", "ברקוד"]
        
        # columns = self.tree["columns"]
        archive_tree = ttk.Treeview(archive_window, columns=columns, show='headings')
        
        for col in columns:
            archive_tree.heading(col, text=col)
            archive_tree.column(col, width=100, anchor=tk.CENTER)
        
        for item in self.archived_items:
            archive_tree.insert('', tk.END, values=item)
        
        print("archive", self.archived_items)
        
        # הוספת כפתור שחזור
        def restore_item():
            selected = archive_tree.selection()
            if not selected:
                messagebox.showwarning("שגיאה", "נא לבחור מוצר לשחזור")
                return
                
            item = archive_tree.item(selected[0])['values']
            idx = self.total_items_in_categories()
            # barcode_value = self.generate_barcode(item)
            print("restore", item)
            # item[14] = barcode_value
            self.tree.insert('', tk.END, values = (idx,) + tuple(item))
            
            self.category_data[self.current_category.get()].append(item)
            
            # הסרה מהארכיון
            item_as_strings = [str(i) for i in item]
            for sublist in self.archived_items:
                if sublist == item_as_strings:
                    self.archived_items.remove(sublist)
                    break 
            archive_tree.delete(selected)
            
            self.save_archive()
            # self.save_data()
            self.update_total()
            
        tk.Button(archive_window, text="שחזר למלאי", command=restore_item).pack(pady=5)
        archive_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def change_category(self, category):
        self.current_category.set(category)
        
        # ניקוי הטבלה
        for item in self.tree.get_children():
            self.tree.delete(item)
        idx = 1
        for item in self.category_data[category]:
            is_archived = False
            for archived_item in self.archived_items:
                if item[:14] == archived_item[:14]:
                    is_archived = True
                    break
            if not is_archived:
                self.tree.insert('', tk.END, values=(idx,) + tuple(item))
                idx += 1
            
        self.update_total()

    def save_data(self):
        """שמירת נתוני הקטגוריות לקובץ"""
        for category in self.categories:
            filename = f'{category}.csv'
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(self.category_data[category])

    def load_data(self):
        """טעינת נתוני הקטגוריות מקבצים"""
        for category in self.categories:
            filename = f'{category}.csv'
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    self.category_data[category] = list(reader)
            except FileNotFoundError:
                self.category_data[category] = []
        
        # טעינת הקטגוריה הנוכחית
        self.change_category(self.current_category.get())
        
    def save_archive(self):
        with open('archive.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(self.archived_items)
            print("delete===", self.archived_items)

    def load_archive(self):
        try:
            with open('archive.csv', 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                self.archived_items = list(reader)
        except FileNotFoundError:
            self.archived_items = []

    def search_products(self, event=None):
        search_term = self.search_entry.get().lower()
        for item in self.tree.get_children():
            if not search_term:
                self.tree.item(item, tags=())
            else:
                values = [str(v).lower() for v in self.tree.item(item)['values']]
                if any(search_term in v for v in values):
                    self.tree.item(item, tags=('found',))
                else:
                    self.tree.item(item, tags=('hidden',))
        
        self.tree.tag_configure('found', background='lightblue')
        self.tree.tag_configure('hidden', background='gray')
    
    def update_total(self):
        total = 0
        for item in self.tree.get_children():
            try:
                price = float(self.tree.item(item)['values'][-2])  # -2 כי עכשיו ברקוד הוא האחרון
                total += price
            except:
                continue
        self.total_label.config(text=f'סה"כ: {total:,.2f} ₪')

    def print_label(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("שגיאה", "נא לבחור מוצר להדפסת מדבקה")
            return
        item = self.tree.item(selected[0])['values']
        barcode_data = item[15] if len(item) > 15 else self.generate_barcode(item)
        
        
        output_filename = filedialog.asksaveasfilename(defaultextension=".pdf",
                                                    filetypes=[("PDF files", "*.pdf"),
                                                               ("All files", "*.*")])
        if output_filename:
            c = canvas.Canvas(output_filename, pagesize=letter)
            width, height = letter
            try:
                pdfmetrics.registerFont(TTFont('HebrewFont', 'Arial.ttf'))
                c.setFont('HebrewFont', 12)
                
                text = f"""
                מספר מוצר: {item[0]}
                מספר סידורי: {item[1]}
                מותג: {item[2]}
                דגם: {item[3]}

                מפרט טכני:
                -----------------
                מסך: {item[4]}
                מעבד: {item[5]}
                זיכרון: {item[6]}
                דיסק: {item[7]}
                כרטיס מסך: {item[8]}
                רזולוציה: {item[9]}
                מסך מגע: {item[10]}
                מערכת הפעלה: {item[11]}
                סטטוס: {item[12]}

                ברקוד: {barcode_data}
                """
                
                barcode_filename = 'barcode'
                code128 = barcode.get('code128', str(barcode_data), writer=ImageWriter())
                code128.save(barcode_filename)
                text_y = height - 50
                for line in text.strip().split('\n'):
                    c.drawString(100, text_y, line.strip())
                    text_y -= 15
                print(text)
                c.drawImage(barcode_filename + '.png', 100, height - 450, width=200, height=120)
                c.save()
            except Exception as e:
                messagebox.showerror("שגיאה", f"שגיאה בהדפסת מדבקה: {str(e)}")

            print(f"PDF created: {output_filename}")
        else:
            print("Save operation canceled.")
            
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = InventorySystem(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("שגיאה", f"שגיאה קריטית: {str(e)}")
