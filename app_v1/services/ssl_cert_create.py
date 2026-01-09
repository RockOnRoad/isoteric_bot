#!/usr/bin/env python3
"""
Одноразовое создание SSL сертификата с помощью Python (без OpenSSL)
"""
import os
import ipaddress
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta, timezone


def create_self_signed_cert(ip_address: str, output_dir: str = "ssl"):
    """Создает самоподписанный SSL сертификат"""

    # Создаем директорию
    os.makedirs(output_dir, exist_ok=True)

    cert_path = os.path.join(output_dir, "certificate.pem")
    key_path = os.path.join(output_dir, "private.key")

    print(f"🔐 Создаем SSL сертификат для IP: {ip_address}")

    try:
        # Генерируем приватный ключ
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        # Создаем сертификат
        subject = issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "RU"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Moscow"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Moscow"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "BananaGen"),
                x509.NameAttribute(NameOID.COMMON_NAME, ip_address),
            ]
        )

        now_utc = datetime.now(timezone.utc)

        ip_obj = ipaddress.ip_address(ip_address)

        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now_utc)
            .not_valid_after(now_utc + timedelta(days=365))
            .add_extension(
                x509.SubjectAlternativeName(
                    [
                        x509.IPAddress(ip_obj),
                    ]
                ),
                critical=False,
            )
            .sign(private_key, hashes.SHA256())
        )

        # Сохраняем приватный ключ
        with open(key_path, "wb") as f:
            f.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )

        # Сохраняем сертификат
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        print("✅ SSL сертификат успешно создан!")
        print(f"📄 Сертификат: {cert_path}")
        print(f"🔑 Приватный ключ: {key_path}")

        return True

    except ImportError:
        print("❌ Необходима библиотека cryptography")
        print("💡 Установите: pip install cryptography")
        return False
    except Exception as e:
        print(f"❌ Ошибка создания сертификата: {e}")
        return False


def main():
    """Основная функция"""
    ip_address = "77.73.235.52"
    output_dir = "ssl"

    success = create_self_signed_cert(ip_address, output_dir)

    if success:
        print("\n📋 Добавьте в .env файл:")
        print(
            f"SSL_CERT_PATH={os.path.abspath(os.path.join(output_dir, 'certificate.pem'))}"
        )
        print(
            f"SSL_KEY_PATH={os.path.abspath(os.path.join(output_dir, 'private.key'))}"
        )
        print(f"WEBHOOK_URL=https://{ip_address}:8443/webhook/yookassa")
        print("\n🎉 Готово! Теперь webhook будет работать по HTTPS")
    else:
        print("\n❌ Не удалось создать сертификат")


if __name__ == "__main__":
    main()
