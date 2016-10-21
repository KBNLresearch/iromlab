import  Queue

        
def main():
    q = Queue.Queue()
    
    q.put("001")
    q.put("002")
    q.put("003")    

    while not q.empty():
        print(q.get())

    print(q)

    while not q.empty():
        print(q.get())
    
main()
