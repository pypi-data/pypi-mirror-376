from ai_text_utils.text import Tokenizer, get_text_from_gutenberg_books, GenTextDataset, LSTMModel, create_dataloader, train_val_split, GutenbergBooks
import torch
from torch.utils.data import DataLoader
import ai_text_utils

def main():
    print(ai_text_utils.__version__)
    '''
    tkn = Tokenizer()

    tokens = tkn.encode("This is an example of tokenization")

    print(f'Tokens={tokens}')
    tokens = torch.Tensor(tokens).numpy()
    tokens=2065.5
    print(f'Getting text back from tokens = {tkn.decode(tokens)}')
    '''
    '''
    txt = get_text_from_gutenberg_books(start_book_id=5000, 
                                        num_books=2, 
                                        keep_headers=False)
    
    print(txt)
    '''

    books = GutenbergBooks("my_gutenberg_books")
    
    # Example usage - choose one of these options:
    
    # Option 1: List of individual book IDs
    #book_ids = [123, 105, 90, 108, 3157]
    
    # Option 2: List of range objects
    book_ids = [
         {'start_id': 1661, 'num_books': 1},
         #{'start_id': 208, 'num_books': 4}
     ]
    
    # Get combined text from all books
    txt = books.get_books(book_ids)

    txt_arr = txt.split("<end_of_text>")

    train_txt = "".join(txt_arr[:9])
    val_txt = "".join(txt_arr[9:])

    seq_len=10
    batch_size=3
    last_token_only=True
    train_dl = create_dataloader(train_txt, 
                                 seq_len=seq_len, 
                                 batch_size=batch_size,
                                 shuffle=True,
                                 last_token_only=last_token_only)

    val_dl = create_dataloader(val_txt, 
                               seq_len=seq_len, 
                               batch_size=batch_size,
                               shuffle=True,
                               last_token_only=last_token_only)

    X, y = next(iter(train_dl))
    print(f'X shape {X}, y shape {y}')

    # 
    # say tokens =[1,2,3,4,5,6,7,8,9,10,11,12]
    # last_token_only=False generates data as ([1,2,3,4,5],[2,3,4,5,6]), ([7,8,9,10,11],[8,9,10,11,12])
    # last_token_only=True generates data as ([1,2,3,4,5],[6]), ([2,3,4,5,6],[7]), ([3,4,5,6,7],[8])
    '''
    tokens = tkn.encode(txt)
    dataset = GenTextDataset(tokens=tokens,last_token_only=False, seq_len=5)
    X,y = dataset[:2]
    print(f'last_token_only=False, X={X}, y={y}')
    dataset = GenTextDataset(tokens=tokens,last_token_only=True, seq_len=5)
    X,y = dataset[:2]
    print(f'last_token_only=True, X={X}, y={y}')
    '''

    '''
    train_txt, val_txt = train_val_split(txt, train_ratio=0.9)
    train_dl = create_dataloader(train_txt, batch_size=3, shuffle=True)
    val_dl=create_dataloader(val_txt, batch_size=3, shuffle=True)
    print(f'Train dl count: {len(train_dl)}, Val dl count: {len(val_dl)}')
    X, y = next(iter(train_dl))
    vocab_size=tkn.vocab_size()

    emb_size=100
    hidden_size=40
    model= LSTMModel(vocab_size=vocab_size,emb_size=emb_size,hidden_size=hidden_size)
    pred = model(X)
    _, pred = torch.max(pred, 1)
    print(f'vocab size = {vocab_size}, pred={pred}, actual={y}')
    '''




