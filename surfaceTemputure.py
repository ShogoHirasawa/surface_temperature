import numpy as np
from osgeo import gdal, osr

def calculate_surface_temperature(band4_path, band5_path, band10_path, band11_path, mtl_path, output_path):
    # バンドの読み込み
    band4 = gdal.Open(band4_path).ReadAsArray().astype(np.float32)
    band5 = gdal.Open(band5_path).ReadAsArray().astype(np.float32)
    band10 = gdal.Open(band10_path).ReadAsArray().astype(np.float32)
    band11 = gdal.Open(band11_path).ReadAsArray().astype(np.float32)

    # 0の値を非常に小さい値で置換
    band5[band5 == 0] = 1e-10
    band11[band11 == 0] = 1e-10

    # MTLファイルの読み込み
    mtl_data = {}
    with open(mtl_path, 'r') as mtl_file:
        for line in mtl_file:
            if line.strip() != '' and '=' in line:
                key, value = line.split('=')
                mtl_data[key.strip()] = value.strip()

    # ラジアンテンパーチャー変換の係数の取得
    K1 = float(mtl_data['RADIANCE_MULT_BAND_10'])
    K2 = float(mtl_data['RADIANCE_ADD_BAND_10'])
    L = float(mtl_data['RADIANCE_MAXIMUM_BAND_10'])
    QCAL = float(mtl_data['QUANTIZE_CAL_MAX_BAND_10'])

    # 地表面温度の計算
    radiance = (band10 * K1) + K2
    radiance = np.maximum(radiance, 0.1)  # ゼロ除算を回避するために最小値を設定
    brightness_temp = L / np.log((QCAL / radiance) + 1)
    surface_temp = brightness_temp / (1 + (np.log(band11 / band5) / 14380))
    
    # ケルビンからセルシウスに変換
    surface_temp = surface_temp - 273.15

    # 出力ファイルの作成と書き込み
    driver = gdal.GetDriverByName('GTiff')
    output_dataset = driver.Create(output_path, band4.shape[1], band4.shape[0], 1, gdal.GDT_Float32)
    
    # ファイル作成が成功したかチェック
    if output_dataset is None:
        print("エラー: ファイルの作成に失敗しました。出力パスを確認してください。")
        return

    output_dataset.GetRasterBand(1).WriteArray(surface_temp)

    # 投影情報の設定（EPSGコードをEPSG:32654に設定）
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(32654)  
    output_dataset.SetProjection(srs.ExportToWkt())
    output_dataset.SetGeoTransform(gdal.Open(band4_path).GetGeoTransform())

    # ファイルを閉じて終了
    output_dataset = None
    print("地表面温度が正常に計算され、ファイルに出力されました。")

# 使用例
band4_path = ''
band5_path = ''
band10_path = ''
band11_path = ''
mtl_path = ''
output_path = ''

calculate_surface_temperature(band4_path, band5_path, band10_path, band11_path, mtl_path, output_path)
