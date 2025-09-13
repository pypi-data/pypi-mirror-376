import unittest

import pytest
from slixmpp.exceptions import XMPPError

from conftest import AvatarFixtureMixin
from slixmpp import JID, Iq

from slidge import BaseGateway, BaseSession, GatewayUser, LegacyRoster, LegacyBookmarks, LegacyMUC, LegacyContact
from slidge.core.session import _sessions
from slidge.util.test import SlidgeTest
from slidge.util.types import LegacyUserIdType, LegacyMUCType, MucType


class Gateway(BaseGateway):
    COMPONENT_NAME = "A test"
    GROUPS = True


class Contact(LegacyContact):
    async def update_info(self):
        if self.legacy_id.startswith("group"):
            raise XMPPError()


class Session(BaseSession):
    async def login(self):
        return "YUP"


class Bookmarks(LegacyBookmarks):
    async def fill(self) -> None:
        pass


class MUC(LegacyMUC):
    async def update_info(self):
        if not self.legacy_id.startswith("group"):
            raise XMPPError()
        self.type = MucType.GROUP

@pytest.mark.usefixtures("avatar")
class TestEmptySubject(AvatarFixtureMixin, SlidgeTest):
    plugin = globals()
    xmpp: Gateway

    def setUp(self):
        super().setUp()
        with self.xmpp.store.session() as orm:
            user = GatewayUser(
                jid=JID("romeo@montague.lit/gajim").bare,
                legacy_module_data={"username": "romeo", "city": ""},
                preferences={"sync_avatar": True, "sync_presence": True},
            )
            orm.add(user)
            orm.commit()
        self.run_coro(
            self.xmpp._BaseGateway__dispatcher._on_user_register(
                Iq(sfrom="romeo@montague.lit/gajim")
            )
        )
        welcome = self.next_sent()
        assert welcome["body"]
        stanza = self.next_sent()
        assert "logging in" in stanza["status"].lower(), stanza
        stanza = self.next_sent()
        assert "syncing contacts" in stanza["status"].lower(), stanza
        stanza = self.next_sent()
        assert "syncing groups" in stanza["status"].lower(), stanza
        probe = self.next_sent()
        assert probe.get_type() == "probe"
        stanza = self.next_sent()
        assert "yup" in stanza["status"].lower(), stanza

        self.send(  # language=XML
            """
            <iq type="get"
                to="romeo@montague.lit"
                id="1"
                from="aim.shakespeare.lit">
              <pubsub xmlns="http://jabber.org/protocol/pubsub">
                <items node="urn:xmpp:avatar:metadata" />
              </pubsub>
            </iq>
            """
        )

    def tearDown(self):
        super().tearDown()
        _sessions.clear()

    @property
    def romeo_session(self) -> Session:
        return BaseSession.get_self_or_unique_subclass().from_jid(
            JID("romeo@montague.lit")
        )

    def test_empty_subject(self):
        muc = self.run_coro(self.romeo_session.bookmarks.by_legacy_id("group"))
        with unittest.mock.patch("slidge.core.mixins.message_maker.uuid4", return_value="uuid"), unittest.mock.patch("uuid.uuid4", return_value="uuid"):
            self.recv(  # language=XML
                f"""
            <presence from="romeo@montague.lit/movim"
                      to="{muc.jid}/nick">
              <x xmlns='http://jabber.org/protocol/muc' />
            </presence>
            """            )
            self.send(  # language=XML
                """
            <presence from="group@aim.shakespeare.lit/romeo"
                      to="romeo@montague.lit/movim">
              <x xmlns="http://jabber.org/protocol/muc#user">
                <item affiliation="member"
                      role="participant"
                      jid="romeo@montague.lit/movim" />
                <status code="210" />
                <status code="110" />
                <status code="100" />
              </x>
              <occupant-id xmlns="urn:xmpp:occupant-id:0"
                           id="slidge-user" />
            </presence>
            """,
            use_values=False)
            self.send(  # language=XML
                """
            <message type="groupchat"
                     from="group@aim.shakespeare.lit"
                     to="romeo@montague.lit/movim">
              <stanza-id xmlns="urn:xmpp:sid:0"
                         id="uuid"
                         by="group@aim.shakespeare.lit" />
              <occupant-id xmlns="urn:xmpp:occupant-id:0"
                           id="room" />
              <subject />
            </message>
            """,
            use_values=False,
            )
