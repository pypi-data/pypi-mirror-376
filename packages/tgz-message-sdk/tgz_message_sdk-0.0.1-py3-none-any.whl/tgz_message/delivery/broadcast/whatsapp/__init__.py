from ...broadcast import BroadCastDelivery


class WhatsappDirect(BroadCastDelivery):

    def __init__(
            self,
            event: str,
            recipients: list[str],
            params: dict
    ):
        super().__init__(
            event,
            recipients,
            params
        )

    def build_payload(self) -> dict:
        return {
            "event": self.event,
            "recipients": self.recipients,
            "params": self.params
        }