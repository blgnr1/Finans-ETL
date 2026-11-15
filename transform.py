import os
from dotenv import load_dotenv
from extract import bob_client
from azure import storage
from datetime import datetime
import io
from urllib.parse import quote_plus # sifrede ozel karakter varsa baglanti bozulmasun diye
from azure.storage.blob import BlobServiceClient
import pandas as pd
from sqlalchemy import create_engine # pandas tablolarini dogrudan sql veritabanina yazmak icin


# 1. ilk olarak data lake e aldigimiz ham veriyi okuyalim (EXTRACT)
from extract import dosya_adi
storage_conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
dosya_adi = f"{datetime.now().strftime('%Y-%m-%d')}_kurlar.csv"

# storage a baglanip hem-veri klasorundeki bugunku dosyayi bulalim
blob_service = BlobServiceClient.from_connection_string(storage_conn_str)
blob_client = blob_service.get_blob_client(
    container="ham-veri", blob=dosya_adi
)

# dosyayi ram de okuyalim
indirilen_veri = blob_client.download_blob().readall().decode("utf-8")
df = pd.read_csv(io.StringIO(indirilen_veri))

# 2. Pandas ile temizlik ve donusum yapalim (TRANSFORM)
df = df.dropna()
df = df[df["Kur_USD"]>0]
df["Yukleme_zamani"] = datetime.now()
usd_try_kuru = df.loc[df["Para_Birimi"] == "TRY", "Kur_USD"].values[0]
df["TRY_Karsiligi"] = round(usd_try_kuru / df["Kur_USD"], 4)

# 3. Azure SQL DATABASE E YAZMA (LOAD)
# bilgileri girelim
server = os.getenv("DB_SERVER")
database = os.getenv("DB_DATABASE")
username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")

# python'un Azure SQL'e bağlanacağı standart ODBC bağlantı cümlesini oluşturalim
odbc_str = (
    "Driver={ODBC Driver 18 for SQL Server};"
    f"Server=tcp:{server},1433;"
    f"Database={database};"
    f"Uid={username};"
    f"Pwd={password};"
    "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
)

# SQLALCHEMY motorunu ayaga kaldiralim
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc_str)}")

# pandas tablosunu dogrudan Azure SQL icinde GunlukKurlar tablosuna basiyoruz
df.to_sql("Gunlukkurlar", con=engine, if_exists="append", index=False)

print(f"Toplam {len(df)} satur veri islendi ve Azure SQL 'GunlukKurlar' tablosuna yazildi")