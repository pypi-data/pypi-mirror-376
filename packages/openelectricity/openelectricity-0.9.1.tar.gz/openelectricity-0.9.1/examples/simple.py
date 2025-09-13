from dotenv import load_dotenv

from openelectricity import OEClient

load_dotenv()


def main():
    client = OEClient()
    results = client.get_facilities()

    for r in results.data:
        print(f"{r.code} - {r.name}")


if __name__ == "__main__":
    main()
