import sys
import requests

API_URL = "http://127.0.0.1:1234/v1/models"


def main():
    try:
        response = requests.get(
            API_URL,
            timeout=(5, 10),
            allow_redirects=False
        )

        response.raise_for_status()

        if response.status_code != 200:
            raise ValueError("Odottamaton HTTP-tilakoodi")

        models = response.json()

        if not isinstance(models, dict):
            raise ValueError("Virheellinen API-vastaus")

        model_list = models.get("data")

        if not isinstance(model_list, list):
            raise ValueError("Virheellinen mallilista")

        for model in model_list:
            if (
                not isinstance(model, dict)
                or not isinstance(model.get("id"), str)
                or not model["id"].strip()
            ):
                raise ValueError("Virheellinen mallin tunniste")

        print("Yhteys LM Studioon onnistui!")

        if not model_list:
            print("Malleja ei löytynyt.")

        for model in model_list:
            print(f"Malli: {model['id']}")

        return 0

    except (requests.RequestException, ValueError) as error:
        print(f"Yhteys tai vastauksen käsittely epäonnistui: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
    