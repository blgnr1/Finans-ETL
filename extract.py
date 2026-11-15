import os
from datetime import datetime
import io
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
import pandas as pd
import requests

load_dotenv()

# api dan gercek doviz verisi cekelim
url = "https://api.exchangerate-api.com/v4/latest/USD"
veri = requests.get(url).json()

# pandas tablosuna cevirelim
df = pd.DataFrame(list(veri["rates"].items()), columns=["Para_Birimi", "Kur_USD"])
df["Tarih"] = datetime.now().strftime("%Y-%m-%d")

# dinamik dosya adi olusturalim
dosya_adi = f"{datetime.now().strftime('%Y-%m-%d')}_kurlar.csv"

# olusturdugumuz pandas tablosunu ramde csv ye cevirip azure a yukleyelim
csv_buffer = io.StringIO() # harddiske kaydetmek yerine ram da bos bir sanal metin dosyasi aciyoruz
df.to_csv(csv_buffer, index=False) # pandas tablosu olan df yi csv olarak csv_buffer in icine yaziyoruz

# azure yukleme yapmak icin storage a giris yapalim
connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

# bu şifreyle Azure Storage hesabına bağlanan ana yönetici nesnesini (blob_service) oluşturuyoruz.
blob_service = BlobServiceClient.from_connection_string(connection_string)

# azure hesabının içindeki hangi klasöre ve hangi isimle yazacağımızı belirtiyoruz.
bob_client = blob_service.get_blob_client(
    container="ham-veri", blob=dosya_adi
)

# ramdaki dosyanin icindeki metni alip buluttaki hedefe yukleyelim
bob_client.upload_blob(csv_buffer.getvalue(), overwrite=True)

print(f"Basarili! {dosya_adi} Azure Data Lake'e yuklendi")
