import { Html5QrcodeScanner } from "html5-qrcode";
import { useEffect } from "react";

interface QrScannerFunc {
  onScan: (result: string) => void;
}

export default function QrScanner({ onScan }: QrScannerFunc) {
  useEffect(() => {
    const scanner = new Html5QrcodeScanner(
      "qr-reader",
      {
        fps: 10,
        qrbox: { width: 250, height: 250 },
      },
      false
    );

    const handleSuccess = (decodedText: string) => {
      console.log("QR code détecté :", decodedText);
      onScan(decodedText);

      scanner.clear().catch((error) => {
        console.error("Erreur lors de l'arrêt du scanner :", error);
      });
      return
    };

    const handleError = (errorMessage: string) => {
        return
    };

    scanner.render(handleSuccess, handleError);

    return () => {
      scanner.clear().catch(() => {});
    };
  }, [onScan]);

  return <div id="qr-reader"/>;
}
