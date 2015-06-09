import functions
import math

class findcommonterms :
    """
    - returns 10% of most frequent words of the articles given summaries
    - return values are unique
    """
    
    def __init__(self):
    	# initliaze summaries list
    	self.summaries = []
    	pass

    def step(self,*args):
    	# append summaries
    	self.summaries.append(args)
    	pass


    def final(self):
        yield ("words",)

        # words dict
        word_counter = {}

        # for every summary
        for k in range(0,len(self.summaries)):
                       
            #split it's words into a list
            l = list(self.summaries[k])
            words =  l[0].split()

            # count frequency
            for word in words:
                if word in word_counter:
                    word_counter[word] += 1		
                else:
                    word_counter[word] = 1

        # sort words by frequency
        frequent_words = sorted(word_counter, key = word_counter.get, reverse = True)
        
        # take 10% of them
        x = (10.0/100.0)*len(word_counter)
        n = int(math.ceil(x))
        top_ten_p = frequent_words[:n]

        for i in top_ten_p:
            yield (i,)

findcommonterms.registered = True