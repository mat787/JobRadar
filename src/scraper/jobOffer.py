

class JobOffer:
    """Model danych reprezentujący pojedynczą ofertę (Data Object)."""

    def __init__(self, offer_data, sub_offer_data):
        self.title = offer_data.get('jobTitle')
        self.company = offer_data.get('companyName')
        self.technologies = offer_data.get('technologies', [])
        self.salary = offer_data.get('salaryDisplayText')
        self.levels = offer_data.get('positionLevels', [])
        self.contracts = offer_data.get('typesOfContract', [])
        self.url = sub_offer_data.get('offerAbsoluteUri', 'Brak')
        self.description = sub_offer_data.get('description', 'Brak')
        self.partition_id = sub_offer_data.get('partitionId', 'Brak')