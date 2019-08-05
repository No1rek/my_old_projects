import lxml.html as html
import requests, json
import re


months = ["January","Feb","March","April","May","June","July","August","September","October","November","December"]

def parse_date(date):
    first, year = date.split(',')
    day = first[-2:]
    month = ("0"+str(months.index(first[:-2])+1))[-2:]

    return f"{year}-{month}-{day}"

def get_last_index():
    x, y = get_hist_index()
    return x[-1], y[-1]

def get_hist_index():
    url = 'https://alternative.me/crypto/fear-and-greed-index/'
    page_text = requests.get(url).text
    page_text = page_text.replace(" ", "").replace("\r\n", "").replace("	", "").replace("\n", "")

    patterns = ['''datasets:[{label:"CryptoFear&GreedIndex",fill:false,backgroundColor:'#ccc',borderColor:'#ccc',data:''',
                ''',}]},options:{responsive:true,tooltips:{mode:'index',intersect:false,},hover''',
                '''<script>varconfig={type:'line',data:{labels:''',
                ''',datasets:[{label:"CryptoFear&GreedIndex",fill:false''']

    y = page_text[page_text.find(patterns[0])+len(patterns[0]):page_text.find(patterns[1])]
    x = page_text[page_text.find(patterns[2])+len(patterns[2]):page_text.find(patterns[3])]
    y = y[2:-2].split('","')
    x = x[2:-2].split('","')
    x = list(map(parse_date, x))

    return x, y


if __name__ == "__main__":
    print(get_hist_index())



