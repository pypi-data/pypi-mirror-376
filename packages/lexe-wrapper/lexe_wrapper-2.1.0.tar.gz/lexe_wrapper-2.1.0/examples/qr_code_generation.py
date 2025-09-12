#!/usr/bin/env python3
"""
QR Code Generation Examples for Lightning Invoices

This shows how to generate QR codes server-side in Python,
though most web apps will generate QR codes in JavaScript on the frontend.
"""

import qrcode
import io
import base64
from lexe_wrapper import LexeManager
import requests


def generate_qr_png(invoice_string, filename="lightning_invoice.png"):
    """
    Generate a QR code PNG file from a Lightning invoice.
    
    Args:
        invoice_string: The BOLT11 Lightning invoice string
        filename: Output filename for the PNG
        
    Returns:
        Path to the generated PNG file
    """
    qr = qrcode.QRCode(
        version=None,  # Auto-determine the size
        error_correction=qrcode.constants.ERROR_CORRECT_M,  # 15% error correction
        box_size=10,
        border=4,
    )
    
    # Add the Lightning invoice data
    qr.add_data(invoice_string)
    qr.make(fit=True)
    
    # Create the image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to file
    img.save(filename)
    print(f"✅ QR code saved to {filename}")
    
    return filename


def generate_qr_base64(invoice_string):
    """
    Generate a base64-encoded QR code for embedding in HTML or APIs.
    
    Args:
        invoice_string: The BOLT11 Lightning invoice string
        
    Returns:
        Base64-encoded data URL string
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    
    qr.add_data(invoice_string)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    data_url = f"data:image/png;base64,{img_base64}"
    
    print(f"✅ Generated base64 QR code (length: {len(data_url)} chars)")
    
    return data_url


def generate_qr_svg(invoice_string):
    """
    Generate an SVG QR code (scalable, smaller file size).
    
    Args:
        invoice_string: The BOLT11 Lightning invoice string
        
    Returns:
        SVG string
    """
    import qrcode.image.svg
    
    # Use SVG path style for smallest file size
    factory = qrcode.image.svg.SvgPathImage
    
    qr = qrcode.QRCode(
        image_factory=factory,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
    )
    
    qr.add_data(invoice_string)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Get SVG string
    stream = io.BytesIO()
    img.save(stream)
    svg_string = stream.getvalue().decode()
    
    print(f"✅ Generated SVG QR code")
    
    return svg_string


def create_invoice_with_qr(amount_sats, description):
    """
    Complete example: Create Lightning invoice and generate QR code.
    """
    print(f"\n💰 Creating invoice for {amount_sats} sats...")
    
    with LexeManager() as lexe:
        lexe.start_sidecar()
        
        # Create Lightning invoice
        response = requests.post("http://localhost:5393/v2/node/create_invoice", json={
            "amount": str(amount_sats),
            "description": description,
            "expiration_secs": 3600  # 1 hour
        })
        
        if response.status_code != 200:
            print(f"❌ Failed to create invoice: {response.text}")
            return None
            
        invoice_data = response.json()
        invoice_string = invoice_data['invoice']
        payment_index = invoice_data['index']
        
        print(f"✅ Invoice created!")
        print(f"📋 Payment index: {payment_index}")
        print(f"⚡ Invoice: {invoice_string[:50]}...")
        
        # Generate QR codes in different formats
        print(f"\n🎯 Generating QR codes...")
        
        # 1. PNG file
        png_file = generate_qr_png(invoice_string, f"invoice_{payment_index}.png")
        
        # 2. Base64 for web embedding
        base64_data = generate_qr_base64(invoice_string)
        
        # 3. SVG for scalable graphics
        svg_data = generate_qr_svg(invoice_string)
        
        return {
            'invoice': invoice_string,
            'payment_index': payment_index,
            'qr_png_file': png_file,
            'qr_base64': base64_data,
            'qr_svg': svg_data
        }


# Flask integration example
def flask_example():
    """
    Example Flask endpoint that returns invoice with QR code.
    """
    from flask import Flask, jsonify, request
    
    app = Flask(__name__)
    
    @app.route('/api/invoice-with-qr', methods=['POST'])
    def create_invoice_endpoint():
        data = request.json
        amount = data.get('amount', 1000)
        description = data.get('description', 'Payment')
        
        # Create invoice
        response = requests.post("http://localhost:5393/v2/node/create_invoice", 
                               json={'amount': str(amount), 'description': description})
        invoice_data = response.json()
        
        # Generate QR code as base64
        qr_data_url = generate_qr_base64(invoice_data['invoice'])
        
        return jsonify({
            'invoice': invoice_data['invoice'],
            'payment_index': invoice_data['index'],
            'qr_code': qr_data_url,  # Frontend can use this directly in <img src="">
            'amount': amount,
            'description': description
        })
    
    return app


if __name__ == "__main__":
    print("⚡ Lightning Invoice QR Code Examples")
    print("=" * 50)
    
    # Check if qrcode is installed
    try:
        import qrcode
        print("✅ qrcode library is installed")
    except ImportError:
        print("❌ Please install qrcode library:")
        print("   pip install qrcode[pil]")
        exit(1)
    
    # Example 1: Generate QR from existing invoice
    print("\n📋 Example 1: Generate QR from existing invoice")
    test_invoice = "lnbc1000n1pn0sjxqpp5test1234567890abcdefghijklmnopqrstuvwxyz"
    generate_qr_png(test_invoice, "test_invoice.png")
    
    # Example 2: Create real invoice with QR (requires running sidecar)
    print("\n📋 Example 2: Create invoice with QR codes")
    print("(This requires a running Lexe sidecar with valid credentials)")
    
    try:
        result = create_invoice_with_qr(1000, "Test payment with QR")
        if result:
            print(f"\n✅ Success! Generated QR codes for invoice")
            print(f"   PNG file: {result['qr_png_file']}")
            print(f"   Base64 length: {len(result['qr_base64'])} chars")
            print(f"   SVG length: {len(result['qr_svg'])} chars")
    except Exception as e:
        print(f"⚠️  Skipping real invoice example: {e}")
        print("   (This is normal if you don't have a Lexe node configured)")
    
    print("\n🎉 Examples complete!")
    print("\n💡 TIP: Most web apps should generate QR codes in JavaScript")
    print("   See payment_qr_demo.html for a complete frontend example")