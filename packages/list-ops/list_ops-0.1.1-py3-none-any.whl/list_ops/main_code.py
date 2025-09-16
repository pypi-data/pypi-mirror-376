import fitz

def get_text_index(text, corpus):

  page_text = corpus.copy()
  page_text = page_text + [''] * len(text.split(' '))

  for i in range(0,len(page_text)-len(text.split(' ')) + 1):
    value = page_text[i]
    for j in range(i+1, i+ len(text.split(' '))+1):

        if value == text:
            # print('value matched...\t',value, ' At index:\t',i,j,'NEXT value is:\t', page_text[i+(j-i)])

            # return the last index 
            return i+(j-i)-1 # to skip the next entry
        
        if j >= len(page_text):
            return -1 # not found
            
        value = (value + ' ' + page_text[j]).strip()

    else: # used with for loop to continue if the inner loop is not broken
        continue

    break # breaks the outer loop


def get_prev_text(text, corpus):
    index = get_text_index(text, corpus)

    if index > 0:
        return corpus[index - 1]
    
    else:
        return None
    
def get_next_text(text, corpus):
    index = get_text_index(text, corpus)

    if index <= len(corpus) - 1:
        return corpus[index + 1]
    
    else:
        return None


if __name__ == "__main__":
   data = ["Hello world this is a", "test", "This is a test Hello world", "Hello Hello world world"]

   index = get_text_index("Hello world this is a test", data)
   print("Index found at: ", index)

