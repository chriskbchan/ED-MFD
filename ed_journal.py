import logging
from common import *
import os, sys
import time
import json
import glob, io
from config import *
from ed_object import *
from ed_status import *
from mfd_interface import *
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

J_PATH = "journals"
J_LOG  = os.path.join(J_PATH, "Journal.*.log")
J_STAT = os.path.join(J_PATH, "Status.json")

class Journal:
    events_monitor = [ "Status", "SupercruiseExit", "Location", "DockingGranted", "Docked", "DockingCancelled", "LoadGame", "ReceiveText", "FSDTarget", "StartJump", "FSDJump" ]
    show_coriolis_types = [ "Coriolis", "Orbis" ]
    path = J_PATH
    patterns = [ J_LOG, J_STAT ]

    @staticmethod
    def openfile(_filename, _seek=None):
        try:
            logger.debug("Open journal: %s" % _filename)
            fh = open(_filename)
            if _seek:
                fh.seek(0, _seek)
        except (OSError, IOError) as e:
            logger.error("Error opening: %s, %s" % (_filename, e))
        return fh

    def parser(journal, ship):
        if journal["event"] in Journal.events_monitor:
            ship.update_event_memory(journal)

    def display(panels, ship, universe, buttons):
        rpanel = panels[0]
        mpanel = panels[1]
        lpanel = panels[2]
        event_memory = ship.get_event_memory()
        try:
            for em in event_memory:
                if ship.event_is_updated(em):				# event is updated
                    #logger.debug("%s has an update" % em)
                    emj = event_memory[em][1]				# retrieve journal content
                    # Status
                    if em == "Status":
                        if "Flags" in emj:
                            ship.update_status_flags(emj["Flags"], buttons, lpanel)
                        if "Pips" in emj:
                            ship.update_status_pips(emj["Pips"], buttons)
                        if "FireGroup" in emj:
                            ship.update_status_firegroup(emj["FireGroup"], buttons)
                        if "GuiFocus" in emj:
                            ship.update_status_guifocus(emj["GuiFocus"], buttons, lpanel)
                        if "Fuel" in emj:
                            ship.update_status_fuel(emj["Fuel"], buttons)
                        if "Cargo" in emj:
                            ship.update_status_cargo(emj["Cargo"], buttons)
                        if "Latitude" in emj:
                            ship.update_status_bearings(emj["Latitude"], emj["Longitude"], emj["Heading"], emj["Altitude"])
                        ship.mark_event_processed(em)
                    # FSDTarget
                    if em == "FSDTarget":
                        ship.mark_event_processed(em)
                    # StartJump
                    if em == "StartJump":
                        ship.mark_event_processed(em)
                    # FSDJump
                    if em == "FSDJump":
                        ship.set_at_system(emj["StarSystem"])
                        ship.mark_event_processed(em)
                    # SupercruiseExit
                    if em == "SupercruiseExit":
                        rpanel.add_text([ "Arrived at %s, %s" % (emj["Body"], emj["StarSystem"]) ])
                        ship.set_at_system(emj["StarSystem"])
                        ship.set_at_station(emj["Body"])
                        show_details_explore(mpanel[MFD.PANEL["EXPLORE"]], ship)
                        ship.mark_event_processed(em)
                    # Location
                    if em == "Location":
                        ship.set_at_system(emj["StarSystem"])
                        if "StationName" in emj:		# if docked
                            ship.set_at_station(emj["StationName"])
                        else:
                            ship.set_at_station(None)
                        show_details_explore(mpanel[MFD.PANEL["EXPLORE"]], ship)
                        ship.mark_event_processed(em)
                    # DockingGranted
                    if em == "DockingGranted":
                        if emj["StationType"] in Journal.show_coriolis_types:
                            mpanel[MFD.PANEL["NORMAL"]].clear_all()
                            mpanel[MFD.PANEL["NORMAL"]].add_coriolis(emj["LandingPad"], Coriolis(MFD_MP_WIDTH))
                        else:
                            station = universe.get_station_data(ship.get_at_station(), ship.get_at_system())
                            if station:
                                pad_layout = station.docking_pad_layout()
                                if pad_layout == 2:
                                    pad_info = station.outpost_pad_info(emj["LandingPad"])
                                    for p in pad_info:
                                        rpanel.add_image("images/" + p)
                        rpanel.add_text([ "Docking granted at pad %s" % emj["LandingPad"] ])
                        ship.mark_event_processed(em)
                    # Docked
                    if em == "Docked":
                        rpanel.add_text([ "Docked at %s, %s" % (emj["StationName"], emj["StarSystem"]) ])
                        draw_logo(mpanel[MFD.PANEL["NORMAL"]])
                        ship.set_at_system(emj["StarSystem"])
                        ship.set_at_station(emj["StationName"])
                        show_details_explore(mpanel[MFD.PANEL["EXPLORE"]], ship)
                        ship.mark_event_processed(em)
                    # DockingCancelled
                    if em == "DockingCancelled":
                        draw_logo(mpanel[MFD.PANEL["NORMAL"]])
                        ship.mark_event_processed(em)
                    # LoadGame
                    if em == "LoadGame":
                        rpanel.add_text([ "Welcome CMDR %s in %s" % (emj["Commander"], emj["ShipName"]) ])
                        ship.mark_event_processed(em)
                    # ReceiveText
                    if em == "ReceiveText":
                        if "STATION_docking_" not in emj["Message"]:
                            if "From_Localised" in emj: _text_from = emj["From_Localised"]
                            else: _text_from = emj["From"]
                            rpanel.add_text([ "%s: %s" % (_text_from, emj["Message_Localised"]) ], color=COLOR_WHITE)
                        ship.mark_event_processed(em)
        except KeyError as e:
            logger.error("KeyError: %s" % e)

class JournalEventHandler(PatternMatchingEventHandler):

    def __init__(self):
        PatternMatchingEventHandler.__init__(self, patterns=Journal.patterns)
        self.captured_events = []
        # Journal log
        list_journals = glob.glob(J_LOG)
        self.journal_latest = max(list_journals, key=os.path.getctime)
        self.journal_fh = Journal.openfile(self.journal_latest, io.SEEK_END)
        # Status json
        self.status_json = J_STAT
        self.status_fh = Journal.openfile(self.status_json)

    def on_any_event(self, event):
        if event.is_directory:
            return None
 
        elif event.event_type == "modified":
            if "Status" in event.src_path:
                logger.debug("Status updated: %s" % event.src_path)
                self.status_process()
            else:
                logger.debug("Journal updated: %s" % event.src_path)
                self.journal_filter()

        elif event.event_type == "created":
            if "Status" in event.src_path:
                logger.debug("Status created: %s" % event.src_path)
                if self.status_fh: self.status_fh.close()
                self.status_json = event.src_path
                self.status_fh = Journal.openfile(self.status_json)
                self.status_process()
            else:
                logger.debug("Journal created: %s" % event.src_path)
                if self.journal_fh: self.journal_fh.close()
                self.journal_latest = event.src_path
                self.journal_fh = Journal.openfile(self.journal_latest)
                self.journal_filter()

        elif event.event_type == "deleted":
            #logger.debug("%s deleted" % event.src_path)
            pass
        else:
            logger.debug("other event: %s: %s" % (event.event_type, event.src_path))

    def status_process(self):
        if self.status_fh:
            try:
                self.status_fh.seek(0, io.SEEK_SET)
                status = json.loads(self.status_fh.readline())
                self.captured_events.append(status)
            except Exception as e:
                logger.debug(e)

    def journal_filter(self):
        jj = self.journal_fh.readline()
        while jj:
            journal = json.loads(jj)
            if 'event' in journal:
                if journal['event'] in Journal.events_monitor:
                    self.captured_events.append(journal)
                    #logger.debug("%s is logged" % journal['event'], flush=True)
                jj = self.journal_fh.readline()

    def get_updates(self):
        return_events = self.captured_events
        self.captured_events = []
        return return_events

