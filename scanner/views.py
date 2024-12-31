from django.shortcuts import render
from .models import QRCode
import qrcode
from django.core.files.storage import FileSystemStorage
from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
from pathlib import Path
from PIL import Image
# from pyzbar.pyzbar import decode

# Create your views here.
def generate_qr(request):
    qr_image_url = None
    if request.method == 'POST':
        mobile_number = request.POST.get('mobile_number')
        data = request.POST.get('qr_data')

        # Validate mobile number
        if not mobile_number or len(mobile_number) != 10 or not mobile_number.isdigit():
            return render(request, 'scanner/generate.html', {'error': 'Invalid Mobile Number'})

        # Generate the QR Code image with data and mobile number
        qr_content = f"{data}|{mobile_number}"
        qr = qrcode.make(qr_content)
        qr_image_io = BytesIO()  # Create a BytesIO Stream
        qr.save(qr_image_io, format='PNG')  # Save the QR code image to qr_image_io
        qr_image_io.seek(0)  # Reset the position of stream to the initial position

        # Define the storage location for the QR Code images
        qr_storage_path = Path(settings.MEDIA_ROOT) / 'qr_codes'
        fs = FileSystemStorage(location=qr_storage_path, base_url='/media/qr_codes/')

        # Ensure the directory exists
        qr_storage_path.mkdir(parents=True, exist_ok=True)

        filename = f"{data}_{mobile_number}.png"
        qr_image_content = ContentFile(qr_image_io.read(), name=filename)
        
        # Save the QR code image to the storage
        fs.save(filename, qr_image_content)
        qr_image_url = fs.url(filename)

        # Save the QR Code data and mobile number in the database
        QRCode.objects.create(data=data, mobile_number=mobile_number)

    return render(request, 'scanner/generate.html', {'qr_image_url': qr_image_url})


def scan_qr(request):
    result = None
    if request.method == 'POST' and request.FILES.get('qr_image'):
        mobile_number = request.POST.get('mobile_number')
        qr_image = request.FILES['qr_image']

        #validate the mobile number
        if not mobile_number or len(mobile_number)!=10 or not mobile_number.isdigit():
            return render(request,'scanner/scan.html',{'error':'Invalid Mobile Number'})
        

        #save the uploaded image
        fs = FileSystemStorage()
        filename = fs.save(qr_image.name,qr_image)
        image_path = Path(fs.location) / filename
        
        try:
            #open the image and decode it
            image = Image.open(image_path)
            decoded_objects = decode(image)

            if decoded_objects:
                #Get the data from the first decoded object
                qr_content = decoded_objects[0].data.decode('utf-8').strip()

                qr_data,qr_mobile_number = qr_content.split('|')

                #check if the data exists in the QRCode model with the provided mobile number

                qr_entry = QRCode.objects.filter(data=qr_data,mobile_number=qr_mobile_number).first()

                if qr_entry and qr_mobile_number==mobile_number:
                    result = "Scan Success: Valid QR Code for the provided Mobile Number"
                    
                    #Delete the specific QR Code entry from the database
                    qr_entry.delete()

                    #Delete the QR Code image from the media/qr_code directory

                    qr_image_path = settings.MEDIA_ROOT / 'qr_codes' / f"{qr_data}_{qr_mobile_number}.png"

                    if qr_image_path.exists():
                        qr_image_path.unlink() #Deletes the QR Code image
                   
                    #Delete the uploaded image from the media folder
                    if image_path.exists():
                        image_path.unlink()
                else:
                    result = "Scan Failed: Invalid QR Code Or Mobile Number Mismatch"            
            else:
                result = "No QR Code detected in the image"
        except Exception as e:
            result = f"Error processing the image:{str(e)}"
            
        finally:
            #Ensure the uploaded image is detected regardless of the result
            if image_path.exists():
                image_path.unlink()


    return render(request, 'scanner/scan.html')
