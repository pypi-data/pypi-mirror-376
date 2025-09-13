import rasterio as rio
from rasterio.enums import Resampling
from rasterio.warp import  reproject
from rasterio import windows
import numpy as np
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from itertools import product



from rasterio.merge import merge
from rasterio.enums import Resampling

def mosaic_images(
    paths: list [str | Path],
    out_tif: str | Path,
    dst_crs: str | None = None,        # ex: "EPSG:4674" (opcional)
    dst_res: float | tuple[float,float] | None = None,  # ex: 10 ou (10,10)
    resampling: Resampling = Resampling.nearest,
    compress: str = "LZW",
    predictor: int = 2,                # 2 p/ inteiros, 3 p/ float
    bigtiff: str = "IF_SAFER",
    tiled: bool = True,
    blocksize: int = 256,
    overviews: bool = True,
):
    """_summary_

    Args:
        paths (list[str  |  Path]): _description_
        out_tif (str | Path): _description_
        dst_crs (str | None, optional): _description_. Defaults to None.
        dst_res (float | tuple[float, float] | None): Output spatial resolution, if None use the resolution of the first index image in the input array. Deafaults to None
        reasampling (Resampling): Resampling method. Default to rasterio.Resampling.nearest
        compress (str, optional): _description_. Defaults to "LZW".
        predictor (int, optional): _description_. Defaults to 2.
        tiled (bool, optional): _description_. Defaults to True.
        blocksize (int, optional): _description_. Defaults to 256.
        overviews (bool, optional): _description_. Defaults to True.

    Raises:
        FileNotFoundError: _description_
    """
    #paths = sorted(map(str, Path().glob(in_dir_glob)))
    if not paths:
        raise FileNotFoundError("Nenhum raster encontrado com esse padrão.")

    srcs = [rio.open(p) for p in paths]

    # Garante NODATA consistente (usa do primeiro arquivo se existir)
    nodata = srcs[0].nodata
    dst_crs = srcs[0].crs
    # Faz o merge (mosaico); reprojeta e resampleia se dst_crs/dst_res informados
    mosaic, out_transform = merge(
        sources=srcs,
        nodata=nodata,
        #dst_crs=dst_crs,
        res=dst_res,
        resampling=resampling,
        method="first"  # ou "last"/"min"/"max"/"sum"/"mean"
    )

    # Perfil de saída
    out_profile = srcs[0].profile.copy()
    for s in srcs: s.close()

    out_profile.update(
        driver="GTiff",
        height=mosaic.shape[1],
        width=mosaic.shape[2],
        dtype='uint16',
        transform=out_transform,
        count=mosaic.shape[0],
        compress=compress,
        predictor=predictor,
        tiled=tiled,
        blockxsize=blocksize,
        blockysize=blocksize,
        BIGTIFF=bigtiff,
        nodata=nodata
    )
    if dst_crs:
        out_profile.update(crs=dst_crs)

    with rio.open(out_tif, "w", **out_profile) as dst:
        dst.write(mosaic)



def resample_image_with_mask(input_fp:str, mask_fp:str, output_fp:str, num_workes=0, resampling_method=Resampling.bilinear, dtype=None, nodata=None) -> None:
    """Resample a input image using a mask image as refence, the output image should have the same pixel size, extent(rows and columns) and projection of the mask image.
        It could be used to crop the input image with the extent of the mask image.


    Args:
        image_fp (str): Filepath of the input image
        mask_fp (str): Filepath of the input image
        output_fp (str): Filepath of the output file
        num_workes (int, optional): Number of parallel workes to use in the resample process. Defaults to 0.
        resampling_method (_type_, optional): _description_. Defaults to Resampling.bilinear.
    """
    # --- 1) Ler referência (grade alvo) ---
    with rio.open(mask_fp) as ref:
        ref_transform = ref.transform
        ref_crs = ref.crs
        ref_height, ref_width = ref.height, ref.width
        out_profile = ref.profile.copy()

    # --- 2) Abrir origem (multi-band) ---
    with rio.open(input_fp) as src:
        nbands = src.count
        src_dtype = src.dtypes[0]  # assume mesmo dtype por banda
        src_nodata = src.nodata

        # Alocar array de saída [bands, rows, cols]
        dst = np.empty((nbands, ref_height, ref_width), dtype=src_dtype)

        # --- 3) Reprojetar cada banda ---
        for b in range(1, nbands + 1):
            reproject(
                source=rio.band(src, b),
                destination=dst[b-1],
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=ref_transform,
                dst_crs=ref_crs,
                resampling=resampling_method,
                dst_nodata=src_nodata,
                num_threads=num_workes,
            )

    if not dtype:
        dtype = src_dtype
    if not nodata:
        nodata = src_nodata

    # --- 4) Gravar saída ---
    out_profile.update({
        "driver": "GTiff",
        "height": ref_height,
        "width": ref_width,
        "transform": ref_transform,
        "crs": ref_crs,
        "count": nbands,
        "dtype": dtype,
        "nodata": nodata,
        # criação recomendada
        "tiled": True,
        "compress": "LZW",
        "predictor": 2 if np.issubdtype(np.dtype(src_dtype), np.floating) else 1,
        "interleave": "band",
        "BIGTIFF": "IF_SAFER",
        "blockxsize": 512,
        "blockysize": 512,
    })

    with rio.open(output_fp, "w", **out_profile) as dst_ds:
        dst_ds.write(dst)


def get_tile_offsets(filepath , win_height=256, win_width=256):
    with rio.open(filepath) as src:
        ncols, nrows  = src.width, src.height
        offsets = product(range(0, ncols, win_width), range(0, nrows, win_height))
        return offsets
    

def get_data_window( filepath, col_off, row_off, width=256, height=256, return_empty=False):
    with rio.open(filepath) as src:
        window = windows.Window(col_off=col_off, row_off=row_off, width=width, height=height)
        data = src.read(window=window)
        meta = get_win_metadata(src, window, width, height)
        if not return_empty:
            empty = check_empty_tile(data)
            if empty:
                return None
        return (data, meta)
    

def get_win_metadata(src, window, width=256, height=256):
    win_transform  = src.window_transform(window)
    meta = src.profile
    meta.update(transform=win_transform,
               width=width,
               height=height)
    return meta

def save_stacked_raster(filepath, data, metadata):
    with rio.open(filepath,'w',**metadata) as dst:
        dst.write(data)


def check_empty_tile(data, no_data=0):
    if  np.all(data == no_data):
        return True
    else:
        return False

def get_tile_window(input_filepath, out_dir, col_off, row_off, window_size = (256,256), return_empty=False):
    """Create and save a tile by a given window size and offset

    Args:
        input_filepath (_type_): _description_
        out_dir (_type_): _description_
        col_off (_type_): _description_
        row_off (_type_): _description_
        window_size (tuple, optional): _description_. Defaults to (256,256).
        return_empty (bool, optional): _description_. Defaults to False.

    Returns:
        _type_: _description_
    """

    filename = input_filepath.stem

    width = window_size[0]
    height = window_size[1]


    # Abra o dataset dentro do processo filho
    with rio.open(input_filepath) as src:
        window = windows.Window(col_off=col_off, row_off=row_off, width=width, height=height)
        data = src.read(window=window)
        meta = get_win_metadata(src, window, width, height)

    #Check if returns empty tiles
    if not return_empty:
        empty = check_empty_tile(data)
        if empty:
            return None

    #return (data, meta)

    
    out_filepath = out_dir.joinpath(f'{filename}_{row_off}_{col_off}').with_suffix('.tif')
    save_stacked_raster(out_filepath,data,meta)

    return str(out_filepath)
    


def create_tiles(input_filepath: str| Path, out_dir: str|Path, tile_size: tuple[int, int]=(256,256), max_workers:int=1):
    """Crop a input raster image in non overlapping tiles by size.

    Args:
        input_filepath (str | Path): input image filepath
        out_dir (str | Path): output directory where the output crop will be saved
        tile_size (tuple[int, int], optional): output tile size (heigth, width). Defaults to (256,256).
        max_workers (int, optional): Number of wokers to parrellize the process. Defaults to 1.
    """
    input_filepath = input_filepath if  isinstance(input_filepath, Path) else Path(input_filepath)
    out_dir = out_dir if isinstance(out_dir, Path) else  Path(out_dir)

    if max_workers == 1:
         for col_off, row_off in get_tile_offsets(input_filepath):
            get_tile_window(input_filepath=input_filepath, out_dir=out_dir, col_off=col_off, row_off=row_off)
    else:
        tasks = []
        with ProcessPoolExecutor(max_workers=max_workers) as ex:
            for col_off, row_off in get_tile_offsets(input_filepath):
                fut = ex.submit(get_tile_window, input_filepath, out_dir, col_off, row_off)
                tasks.append(fut)
            for fut in as_completed(tasks):
                _ = fut.result()  # levanta exceção se der erro; opcional: log