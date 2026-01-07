from Service import ocr_image, determine_orientation, get_image_url, load_image
from utils import save_json, save_failed_ids, read_json
from Models import OCRData, OCRDataList
from pathlib import Path
from tqdm import tqdm

DATA_DIR = Path(__file__).parent.parent.parent / "data"

def process_images(folder_path: Path, orientation_file: Path):
    ocr_data_list = []
    failed_ids = []
    
    orientations = read_json(orientation_file)

    image_extensions = {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.JPG', '.JPEG', '.PNG', '.TIF', '.TIFF'}
    images = [f for f in folder_path.iterdir() if f.suffix in image_extensions]
    
    for image_path in tqdm(images, desc="Processing images"):
        name = image_path.name
        url = get_image_url(name)
        
        try:
            image = load_image(image_path)
            transcript = ocr_image(image_path.stem)
            orientation = determine_orientation(orientations[name])
            ocr_data = OCRData(
                name=name, 
                url=url, 
                transcript=transcript, 
                orientation=orientation
            )
            ocr_data_list.append(ocr_data)
        except Exception as e:
            print(f"\nError processing {name}: {e}")
            failed_ids.append(name)
    
    DATA_DIR.mkdir(exist_ok=True)
    
    validated_data = OCRDataList(ocr_data_list)
    save_json(validated_data.model_dump(mode="json"), DATA_DIR / "b1.json")
    save_failed_ids(failed_ids, DATA_DIR / "failed_b1.txt")
    
    print(f"\nProcessed: {len(ocr_data_list)} images")
    print(f"Failed: {len(failed_ids)} images")

if __name__ == "__main__":
    folder_path = Path("/Users/tashitsering/Downloads/B1")
    orientation_file = DATA_DIR / "b1-orientations.json"
    process_images(folder_path, orientation_file)