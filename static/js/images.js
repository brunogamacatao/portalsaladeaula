function resize_img_fn(img){
    var maxWidth  = 50;           // Max width for the image
    var maxHeight = 50;           // Max height for the image
    var ratio     = 0;            // Used for aspect ratio
    var width     = img.width();  // Current image width
    var height    = img.height(); // Current image height

    // Check if the current width is larger than the max
    if(width > maxWidth){
        ratio = maxWidth / width;          // get ratio for scaling image
        img.css("width", maxWidth);        // Set new width
        img.css("height", height * ratio); // Scale height based on ratio
        height = height * ratio;           // Reset height to match scaled image
        width = width * ratio;             // Reset width to match scaled image
    }

    // Check if current height is larger than max
    if(height > maxHeight){
        ratio = maxHeight / height;      // get ratio for scaling image
        img.css("height", maxHeight);    // Set new height
        img.css("width", width * ratio); // Scale width based on ratio
        width = width * ratio;           // Reset width to match scaled image
    }
};
