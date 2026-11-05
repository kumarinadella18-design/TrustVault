
import cloudinary
import cloudinary.uploader
import cloudinary.utils


def upload_to_cloudinary(uploaded_file):
    result = cloudinary.uploader.upload(
        uploaded_file,
        resource_type="raw",
        type="authenticated"
    )

    return result["public_id"]


def get_cloudinary_download_url(public_id, filename):
    return cloudinary.utils.private_download_url(
        public_id,
        filename.rsplit(".", 1)[-1],
        resource_type="raw",
        type="authenticated",
        attachment=True
    )
