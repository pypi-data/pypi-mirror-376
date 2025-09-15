from ...direct import DirectDelivery


class WhatsappDirect(DirectDelivery):

    def __init__(
            self,
            event: str,
            recipient: str,
            params: dict
    ):
        super().__init__(
            event,
            recipient,
            params
        )

    def build_payload(self) -> dict:
        return {
            "event": self.event,
            "recipient": self.recipient,
            "params": self.params
        }