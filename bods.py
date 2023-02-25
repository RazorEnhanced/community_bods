

cont_serial = Player.Backpack.Serial
cont = Items.FindBySerial(cont_serial)
    

def test():
    books = Bodbook.GetBodbooks(cont.Serial)
    for book in books:
        book.Scan()
        book.Report()

        
        
class Bod:
    # Color of bods
    Blacksmith = 0x044E # Gray
    Tailoring = 0x0000 # Dark green 
    
    materials = {
        Blacksmith:['iron','dull copper','shadow iron','copper','bronze','golden','agaphite','verite','valorite'],
        Tailoring: ['cloth','leather','spined','horned','barbed']
    }
    
    
    def __init__(self):
        self.kind = None
        self.count = 0
        self.items = []
        self.large = False
        self.exceptional = False
        
        self.material = ""
        self.price = -1
        
        self.book_serial = -1
        self.book_page = -1
        self.deed_serial = -1
        self.position_in_page = -1
    
    @staticmethod
    def MaterialToKind(material):
        for kind, mats in Bod.materials.items():
            if material in mats:
                return kind
        return None
        
    def __str__(self):
        bod_size = "small" if self.count == 1 else "LARGE"
        names = [b[0] for b in self.items]
        return "bod {} {} {}\n{}".format(bod_size, self.material, self.exceptional, names)
        
        
        
class Bodbook:
    GumpID = 1425364447
    ItemID = 0x2259
    
    # book
    BtnClose = 0
    BtnFilter = 1
    BtnPrev = 2
    BtnNext = 3
    
    # filter
    
    
    # Factory +-
    
    @staticmethod
    def GetBodbooks(container = None):
        if container is None:
            container = Player.Backpack.Serial
        container = Items.FindBySerial(container)
        if container is None: return None
        
        if len(container.Contains) == 0: 
            Items.UseItem(container)
            Misc.Pause(750)
        
        books = []
        for itm in container.Contains:
            if itm.ItemID != Bodbook.ItemID: continue
            books.append(Bodbook(itm))
        return books
    
    # Bodbook    
    
    def __init__(self,book):
        if isinstance(book, int):
            self.book = Items.FindBySerial(book)
        else:
            self.book = book
            
        if self.book is None:
            Player.HeadMessage(138,"[ERROR] Init: book must be an Item or a Serial")
        
        self.serial = self.book.Serial
            
        self.bods = []
        self.large = []
        self.small = []
        
    
        
    def DeedsInBook(self):
        return Items.GetPropValue(self.book,'Deeds In Book')
        
    def Scan(self):
        num_deeds = self.DeedsInBook()
        if num_deeds == 0:
            Player.HeadMessage(138,"Book is Empty")
            return False
        #scan all pages
        self.Open()        
        page = 1
        hasNext = True
        while hasNext:
            bods, hasNext = self.ScanPage()
            for bod in bods: 
                bod.book_serial = self.serial
                bod.book_page = page
            
            self.bods.extend(bods)
            
            if hasNext: 
                self.NextPage()
                page += 1
        self.Close()
        
            
    def ScanPage(self):
        lines = self.CurrentGumpLines()
        if not self.GumpIsValidBook(lines): 
            return [],False
        
        bods = self.GumpReadBods(lines)
        hasNext = self.GumpHasNext(lines)
        
        return bods,hasNext
            
            
        
    def Report(self):
        small = 0
        large = 0
        normal = 0
        exceptional = 0
        material = {}
        
        for bod in self.bods:
            if len(bod.items)>1:
                large += 1
            else:
                small += 1
                
            if bod.exceptional: 
                exceptional+=1
            else:
                normal += 1
            if bod.material not in material: material[bod.material] = 0
            material[bod.material] += 1
        #
            
        Misc.SendMessage("REPORT",40)
        Misc.SendMessage("Small: {}".format(small),20)
        Misc.SendMessage("Large: {}".format(large),20)
        Misc.SendMessage("Normal: {}".format(normal),60)
        Misc.SendMessage("Exceptional: {}".format(exceptional),60)
        Misc.SendMessage("")
        Misc.SendMessage("MATERIALS",40)
        for name, cnt in material.items():
            Misc.SendMessage("{}: {}".format(name, cnt),50)
        
    
    ## Use gump
    
    def IsOpen(self):
        return Gumps.CurrentGump() == Bodbook.GumpID
        
    def Open(self):
        if not self.IsOpen():
            Items.UseItem(self.book)
            Gumps.WaitForGump(Bodbook.GumpID,1000)
            
    def Close(self):
        if self.IsOpen(): Gumps.SendAction(Bodbook.GumpID,Bodbook.BtnClose)
        
    def PrevPage(self):
        if not self.IsOpen(): return False
        Gumps.SendAction(Bodbook.GumpID,Bodbook.BtnPrev)
        Gumps.WaitForGump(Bodbook.GumpID,1000)
            
    def NextPage(self):
        if not self.IsOpen(): return False
        Gumps.SendAction(Bodbook.GumpID,Bodbook.BtnNext)
        Gumps.WaitForGump(Bodbook.GumpID,1000)
    
    
    
        
    ## Read gump
    
    def TakeDeed(self,position):
        btnTake_base = 5
        step = 2
        btnNum = base + ( position * step )
        Gumps.SendAction(Bodbook.GumpID,btnNum)
        Gumps.WaitForGump(Bodbook.GumpID,1000)
        
    def CurrentGumpLines(self):
        return [str(line).lower().strip() for line in Gumps.LastGumpGetLineList()]
    
    def GumpIsValidFilter(self,lines):
        if lines[0] != 'filter preference': return False
        if lines[-1] != 'apply': return False
        return True
        
    def GumpIsValidBook(self,lines):
        if lines[0] != 'bulk order book': return False
        if lines[11] != 'set': return False
        return True
        
    def GumpHasPrev(self,lines):
        return 'previous page' == lines[12]
        
    def GumpHasNext(self,lines):
        return 'next page' in (lines[12], lines[13])
        
    def GumpReadBods(self,lines):
        content_start = 12
        if self.GumpHasPrev(lines): content_start +=1
        if self.GumpHasNext(lines): content_start +=1
        
        amounts_start=0
        for line in lines:
            amounts_start += 1
            if 'price all</font>' in line: break
        
        content = lines[content_start:amounts_start]
        amounts = lines[amounts_start:]
        
        position_in_page = 0
        bods = []
        bod = None
        for amount in amounts:
            if " / " in amount:
                parts = amount.split(" / ")
                cur = int(parts[0].strip())
                max = int(parts[1].strip())
                bod.items.append( ["",cur,max] )
                bod.count += 1
            else:
                bod = Bod()
                bods.append(bod)
                bod.price = int(amount.strip())
                bod.position_in_page = position_in_page
            #
            position_in_page += 1
            
        cur_line = 0
        for bod in bods:
            cur_line += 1
            bod.exceptional = content[cur_line+1]
            bod.material = content[cur_line+2]
            bod.kind = Bod.MaterialToKind(bod.material)
            for i in range(bod.count):
                bod.items[i][0] = content[cur_line]
                cur_line += 3
            #
            
            #if bod.count > 1:
            #    Misc.SendMessage("{}".format(bod),172)
        
        return bods

    
  
if __name__ == '__main__':     
    test()
