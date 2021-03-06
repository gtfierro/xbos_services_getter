import grpc

from xbos_services_getter.lib import discomfort_pb2
from xbos_services_getter.lib import discomfort_pb2_grpc
from xbos_services_getter.lib import hvac_consumption_pb2
from xbos_services_getter.lib import hvac_consumption_pb2_grpc
from xbos_services_getter.lib import indoor_temperature_action_pb2
from xbos_services_getter.lib import indoor_temperature_action_pb2_grpc
from xbos_services_getter.lib import occupancy_pb2
from xbos_services_getter.lib import occupancy_pb2_grpc
from xbos_services_getter.lib import outdoor_temperature_historical_pb2
from xbos_services_getter.lib import outdoor_temperature_historical_pb2_grpc
# from xbos_services_getter.lib import outdoor_temperature_prediction_pb2
# from xbos_services_getter.lib import outdoor_temperature_prediction_pb2_grpc
from xbos_services_getter.lib import price_pb2
from xbos_services_getter.lib import price_pb2_grpc
from xbos_services_getter.lib import schedules_pb2
from xbos_services_getter.lib import schedules_pb2_grpc
from xbos_services_getter.lib import indoor_temperature_prediction_pb2
from xbos_services_getter.lib import indoor_temperature_prediction_pb2_grpc
from xbos_services_getter.lib import building_zone_names_pb2
from xbos_services_getter.lib import building_zone_names_pb2_grpc

import datetime
import pytz
import pandas as pd

import os

'''
Utility constants
'''
NO_ACTION = 0
HEATING_ACTION = 1
COOLING_ACTION = 2
FAN = 3
TWO_STAGE_HEATING_ACTION = 4
TWO_STAGE_COOLING_ACTION = 5

def get_window_in_sec(s):
    """Returns number of seconds in a given duration or zero if it fails.
    Supported durations are seconds (s), minutes (m), hours (h), and days(d)."""
    seconds_per_unit = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    try:
        return int(float(s[:-1])) * seconds_per_unit[s[-1]]
    except:
        return 0


# Building and Zone names
def get_building_zone_names_stub(BUILDING_ZONE_NAMES_HOST_ADDRESS=None):
    """Get the stub to interact with the building_zone_address service.

    :param BUILDING_ZONE_NAMES_HOST_ADDRESS: Optional argument to supply host address for given service. Otherwise,
        set as environment variable.
    :return: grpc Stub object.

    """

    if BUILDING_ZONE_NAMES_HOST_ADDRESS is None:
        BUILDING_ZONE_NAMES_HOST_ADDRESS = os.environ["BUILDING_ZONE_NAMES_HOST_ADDRESS"]

    credentials = grpc.ssl_channel_credentials()
    channel = grpc.secure_channel(BUILDING_ZONE_NAMES_HOST_ADDRESS, credentials)
    stub = building_zone_names_pb2_grpc.BuildingZoneNamesStub(channel)
    return stub


def get_buildings(building_zone_names_stub):
    """Gets all the building names supported by the services.

    :param building_zone_names_stub: grpc stub for building_zone_names service.
    :return: list (string) building names.

    """

    building_names = building_zone_names_stub.GetBuildings(building_zone_names_pb2.BuildingRequest())
    return [bldg.name for bldg in building_names.names]


def get_zones(building_zone_names_stub, building):
    """Gets all zone names for the given building which are supported by the services.

    :param building_zone_names_stub: grpc stub for building_zone_names service.
    :param building: (string) building name. Needs to be in the list returned by get_buildings.
    :return: list (string) zone names.

    """
    zones = building_zone_names_stub.GetZones(building_zone_names_pb2.ZoneRequest(building=building))
    return [zone.name for zone in zones.names]


def get_all_buildings_zones(building_zone_names_stub):
    """Gets all building and corresponding zones in a dictionary.

    :param building_zone_names_stub: grpc stub for building_zone_names service.
    :return: dictionary <building name, list<zone names>> (strings)

    """
    buildings = get_buildings(building_zone_names_stub)
    zones = {}

    for bldg in buildings:
        zones[bldg] = get_zones(building_zone_names_stub, bldg)

    return zones


# Temperature band functions
def get_temperature_band_stub(TEMPERATURE_BANDS_HOST_ADDRESS=None):
    """Get the stub to interact with the temperature_band service.

    :param TEMPERATURE_BANDS_HOST_ADDRESS: Optional argument to supply host address for given service. Otherwise,
        set as environment variable.
    :return: grpc Stub object.

    """

    if TEMPERATURE_BANDS_HOST_ADDRESS is None:
        TEMPERATURE_BANDS_HOST_ADDRESS = os.environ["TEMPERATURE_BANDS_HOST_ADDRESS"]

    credentials = grpc.ssl_channel_credentials()
    temperature_band_channel = grpc.secure_channel(TEMPERATURE_BANDS_HOST_ADDRESS, credentials)
    temperature_band_stub = schedules_pb2_grpc.SchedulesStub(temperature_band_channel)
    return temperature_band_stub


def get_comfortband(temperature_band_stub, building, zone, start, end, window):
    """Gets comfortband as pd.df.

    :param temperature_band_stub: grpc stub for temperature_band microservice
    :param building: (str) building name
    :param zone: (str) zone name
    :param start: (datetime timezone aware) start of comfortband
    :param end: (datetime timezone aware) end of comfortband
    :param window: (str) the interval in which to split the comfortband.
    :return: pd.df columns=["t_low", "t_high"], valus=float, index=time

    """
    start_unix = start.timestamp() * 1e9
    end_unix = end.timestamp() * 1e9
    window_seconds = get_window_in_sec(window)

    # call service
    comfortband_response = temperature_band_stub.GetComfortband(
        schedules_pb2.Request(building=building, zone=zone, start=int(start_unix), end=int(end_unix), window=window,
                              unit="F"))

    # process data
    comfortband_final = pd.DataFrame(columns=["t_high", "t_low"],
                                     index=pd.date_range(start, end, freq=str(window_seconds) + "S"))[:-1]
    for msg in comfortband_response.schedules:
        msg_datetime = datetime.datetime.utcfromtimestamp(msg.time / 1e9).replace(tzinfo=pytz.utc).astimezone(
            tz=start.tzinfo)
        comfortband_final.loc[msg_datetime]["t_high"] = msg.temperature_high
        comfortband_final.loc[msg_datetime]["t_low"] = msg.temperature_low

    return comfortband_final


def get_do_not_exceed(temperature_band_stub, building, zone, start, end, window):
    """Gets do_not_exceed as pd.df.

    :param temperature_band_stub: grpc stub for temperature_band microservice
    :param building: (str) building name
    :param zone: (str) zone name
    :param start: (datetime timezone aware) start of do_not_exceed
    :param end: (datetime timezone aware) end of do_not_exceed
    :param window: (str) the interval in which to split the do_not_exceed.
    :return: pd.df columns=["t_low", "t_high"], valus=float, index=time

    """
    start_unix = start.timestamp() * 1e9
    end_unix = end.timestamp() * 1e9
    window_seconds = get_window_in_sec(window)

    # call service
    do_not_exceed_response = temperature_band_stub.GetDoNotExceed(
        schedules_pb2.Request(building=building, zone=zone, start=int(start_unix), end=int(end_unix), window=window,
                              unit="F"))

    # process data
    do_not_exceed_final = pd.DataFrame(columns=["t_high", "t_low"],
                                       index=pd.date_range(start, end, freq=str(window_seconds) + "S"))[:-1]
    for msg in do_not_exceed_response.schedules:
        msg_datetime = datetime.datetime.utcfromtimestamp(msg.time / 1e9).replace(tzinfo=pytz.utc).astimezone(
            tz=start.tzinfo)
        do_not_exceed_final.loc[msg_datetime]["t_high"] = msg.temperature_high
        do_not_exceed_final.loc[msg_datetime]["t_low"] = msg.temperature_low

    return do_not_exceed_final


# occupancy functions
def get_occupancy_stub(OCCUPANCY_HOST_ADDRESS=None):
    """Get the stub to interact with the occupancy service.

    :param OCCUPANCY_HOST_ADDRESS: Optional argument to supply host address for given service. Otherwise,
        set as environment variable.
    :return: grpc Stub object.

    """
    if OCCUPANCY_HOST_ADDRESS is None:
        OCCUPANCY_HOST_ADDRESS = os.environ["OCCUPANCY_HOST_ADDRESS"]

    credentials = grpc.ssl_channel_credentials()
    occupancy_channel = grpc.secure_channel(OCCUPANCY_HOST_ADDRESS, credentials)
    return occupancy_pb2_grpc.OccupancyStub(occupancy_channel)


def get_occupancy(occupancy_stub, building, zone, start, end, window):
    """Gets occupancy as pd.series.

    :param occupancy_stub: grpc stub for occupancy microservice
    :param building: (str) building name
    :param zone: (str) zone name
    :param start: (datetime timezone aware)
    :param end: (datetime timezone aware)
    :param window: (str) the interval in which to split the data.
    :return: pd.series valus=float, index=time

    """

    start_unix = start.timestamp() * 1e9
    end_unix = end.timestamp() * 1e9
    window_seconds = get_window_in_sec(window)

    # call service
    occupancy_response = occupancy_stub.GetOccupancy(
        occupancy_pb2.Request(building=building, zone=zone, start=int(start_unix), end=int(end_unix), window=window))

    # process data
    occupancy_final = pd.Series(index=pd.date_range(start, end, freq=str(window_seconds) + "S"))[:-1]
    for msg in occupancy_response.occupancies:
        msg_datetime = datetime.datetime.utcfromtimestamp(msg.time / 1e9).replace(tzinfo=pytz.utc).astimezone(
            tz=start.tzinfo)
        occupancy_final.loc[msg_datetime] = msg.occupancy

    return occupancy_final


# price functions
def get_price_stub(PRICE_HOST_ADDRESS=None):
    """Get the stub to interact with the price service.

    :param PRICEPRICE_HOST_ADDRESS: Optional argument to supply host address for given service. Otherwise,
        set as environment variable.
    :return: grpc Stub object.

    """
    if PRICE_HOST_ADDRESS is None:
        PRICE_HOST_ADDRESS = os.environ["PRICE_HOST_ADDRESS"]

    credentials = grpc.ssl_channel_credentials()
    price_channel = grpc.secure_channel(PRICE_HOST_ADDRESS, credentials)
    return price_pb2_grpc.PriceStub(price_channel)


def get_tariff_and_utility(price_stub, building):
    """Gets the tariff and utility for the given building as a dictionary.

    :param price_stub: grpc stub for price microservice
    :param building: (str) building name
    :return: (dictionary) keys=["tariff", "utility"]
    """
    tariff_and_utility = price_stub.GetTariffAndUtility(price_pb2.BuildingRequest(building=building))
    return {"tariff": tariff_and_utility.tariff, "utility": tariff_and_utility.utility}


def get_price(price_stub, building, price_type, start, end, window):
    """Gets the price as a pandas dataframe.

    :param price_stub: grpc stub for price microservice
    :param building: (str) building name
    :param price_type: (str) "ENERGY" or "DEMAND"
    :param start: (datetime timezone aware)
    :param end: (datetime timezone aware)
    :param window: (str) the interval in which to split the data.
    :return: pd.DataFrame columns=["price" (float), "unit" string] index=start to end with window intervals.
    """
    if price_type not in ["ENERGY", "DEMAND"]:
        raise AttributeError("Given price type is invalid. Use ENERGY or DEMAND.")

    start_unix = int(start.timestamp() * 1e9)
    end_unix = int(end.timestamp() * 1e9)
    window_seconds = get_window_in_sec(window)

    # call service
    tariff_and_utility = get_tariff_and_utility(price_stub, building)
    price_response = price_stub.GetPrice(price_pb2.PriceRequest(utility=tariff_and_utility["utility"],
                                                       tariff=tariff_and_utility["tariff"],
                                                       price_type=price_type,
                                                       start=start_unix,
                                                       end=end_unix,
                                                       window=window))

    # process data
    price_final = pd.DataFrame(columns=["price", "unit"], index=pd.date_range(start, end, freq=str(window_seconds) + "S"))[:-1]
    for msg in price_response.prices:
        msg_datetime = datetime.datetime.utcfromtimestamp(msg.time / 1e9).replace(tzinfo=pytz.utc).astimezone(
            tz=start.tzinfo)
        price_final.loc[msg_datetime]["price"] = msg.price
        price_final.loc[msg_datetime]["unit"] = msg.unit

    return price_final


# discomfort functions
def get_discomfort_stub(DISCOMFORT_HOST_ADDRESS=None):
    """Get the stub to interact with the discomfort service.

    :param DISCOMFORT_HOST_ADDRESS: Optional argument to supply host address for given service. Otherwise,
     set as environment variable.
    :return: grpc Stub object.

    """

    if DISCOMFORT_HOST_ADDRESS is None:
        DISCOMFORT_HOST_ADDRESS = os.environ["DISCOMFORT_HOST_ADDRESS"]

    credentials = grpc.ssl_channel_credentials()
    discomfort_channel = grpc.secure_channel(DISCOMFORT_HOST_ADDRESS, credentials)
    return discomfort_pb2_grpc.DiscomfortStub(discomfort_channel)


def get_discomfort(discomfort_stub, building, temperature, temperature_low, temperature_high, occupancy):
    discomfort_response = discomfort_stub.GetLinearDiscomfort(discomfort_pb2.Request(building=building,
                                                                                    temperature=temperature,
                                                                                    temperature_low=temperature_low,
                                                                                    temperature_high=temperature_high,
                                                                                    unit="F",
                                                                                    occupancy=occupancy))
    return discomfort_response.cost


# indoor historic functions
def get_indoor_historic_stub(INDOOR_DATA_HISTORICAL_HOST_ADDRESS=None):
    """Get the stub to interact with the indoor_data_historical service.

    :param INDOOR_DATA_HISTORICAL_HOST_ADDRESS: Optional argument to supply host address for given service. Otherwise,
        set as environment variable.
    :return: grpc Stub object.

    """

    if INDOOR_DATA_HISTORICAL_HOST_ADDRESS is None:
        INDOOR_DATA_HISTORICAL_HOST_ADDRESS = os.environ["INDOOR_DATA_HISTORICAL_HOST_ADDRESS"]

    credentials = grpc.ssl_channel_credentials()
    indoor_historic_channel = grpc.secure_channel(INDOOR_DATA_HISTORICAL_HOST_ADDRESS, credentials)
    return indoor_temperature_action_pb2_grpc.IndoorTemperatureActionStub(indoor_historic_channel)


def get_indoor_temperature_historic(indoor_historic_stub, building, zone, start, end, window):
    """Gets historic indoor temperature as pd.series.

    :param indoor_historic_stub: grpc stub for historic indoor temperature microservice
    :param building: (str) building name
    :param zone: (str) zone name
    :param start: (datetime timezone aware)
    :param end: (datetime timezone aware)
    :param window: (str) the interval in which to split the data.
    :return: pd.series valus=float, index=time

    """
    start_unix = int(start.timestamp() * 1e9)
    end_unix = int(end.timestamp() * 1e9)
    window_seconds = get_window_in_sec(window)

    # call service
    historic_indoor_response = indoor_historic_stub.GetRawTemperatures(
        indoor_temperature_action_pb2.Request(building=building, zone=zone, start=start_unix, end=end_unix,
                                              window=window))

    # process data
    historic_indoor_final = pd.Series(index=pd.date_range(start, end, freq=str(window_seconds) + "S"))[:-1]
    for msg in historic_indoor_response.temperatures:
        msg_datetime = datetime.datetime.utcfromtimestamp(msg.time / 1e9).replace(tzinfo=pytz.utc).astimezone(
            tz=start.tzinfo)
        historic_indoor_final.loc[msg_datetime] = msg.temperature

    return historic_indoor_final


def get_actions_historic(indoor_historic_stub, building, zone, start, end, window):
    """Gets historic indoor temperature as pd.series.

    :param indoor_historic_stub: grpc stub for historic indoor temperature microservice
    :param building: (str) building name
    :param zone: (str) zone name
    :param start: (datetime timezone aware)
    :param end: (datetime timezone aware)
    :param window: (str) the interval in which to split the data.
    :return: pd.series valus=float, index=time

    """
    start_unix = int(start.timestamp() * 1e9)
    end_unix = int(end.timestamp() * 1e9)
    window_seconds = get_window_in_sec(window)

    # call service
    historic_action_response = indoor_historic_stub.GetRawActions(
        indoor_temperature_action_pb2.Request(building=building, zone=zone, start=start_unix, end=end_unix,
                                              window=window))

    # process data
    historic_action_final = pd.Series(index=pd.date_range(start, end, freq=str(window_seconds) + "S"))[:-1]
    for msg in historic_action_response.actions:
        msg_datetime = datetime.datetime.utcfromtimestamp(msg.time / 1e9).replace(tzinfo=pytz.utc).astimezone(
            tz=start.tzinfo)
        historic_action_final.loc[msg_datetime] = msg.action

    return historic_action_final


# indoor historic functions
def get_indoor_temperature_prediction_stub(INDOOR_TEMPERATURE_PREDICTION_HOST_ADDRESS=None):
    """Get the stub to interact with the indoor_temperature_prediction service.

    :param INDOOR_TEMPERATURE_PREDICTION_HOST_ADDRESS: Optional argument to supply host address for given service. Otherwise,
        set as environment variable.
    :return: grpc Stub object.

    """

    if INDOOR_TEMPERATURE_PREDICTION_HOST_ADDRESS is None:
        INDOOR_TEMPERATURE_PREDICTION_HOST_ADDRESS = os.environ["INDOOR_TEMPERATURE_PREDICTION_HOST_ADDRESS"]

    credentials = grpc.ssl_channel_credentials()
    indoor_temperature_prediction_channel = grpc.secure_channel(INDOOR_TEMPERATURE_PREDICTION_HOST_ADDRESS, credentials)
    return indoor_temperature_prediction_pb2_grpc.IndoorTemperaturePredictionStub(indoor_temperature_prediction_channel)


def get_indoor_temperature_prediction(indoor_temperature_prediction_stub, building, zone, current_time, action, t_in, t_out, t_prev,
                                      other_zone_temperatures):
    """Gets prediction of indoor temperature.

    :param indoor_temperature_prediction_stub: grpc stub for prediction of indoor temperature microservice
    :param building: (str) building name
    :param zone: (str) zone name
    :param current_time: (datetime timezone aware)
    :param action: (int) Action as given in utils file.
    :param t_in: (float) current temperature inside of zone.
    :param t_out: (float) currrent outdoor temperature.
    :param t_prev: (float) the temperature 5 min ago.
    :param other_zone_temperatures: {zone_i: indoor temperature of zone_i}
    :return: (float) temperature in 5 minutes after current_time in Fahrenheit.

    """
    current_time_unix = int(current_time.timestamp() * 1e9)

    # call service
    indoor_prediction_response = indoor_temperature_prediction_stub.GetSecondOrderPrediction(
        indoor_temperature_prediction_pb2.SecondOrderPredictionRequest(building=building, zone=zone, current_time=current_time_unix,
                                              action=action,
                                              indoor_temperature=t_in, previous_indoor_temperature=t_prev,
                                                                       outside_temperature=t_out,
                                              other_zone_temperatures=other_zone_temperatures,
                                              temperature_unit="F"))

    return indoor_prediction_response.temperature


# HVAC Consumption functions
def get_hvac_consumption_stub(HVAC_CONSUMPTION_HOST_ADDRESS=None):
    """Get the stub to interact with the hvac_consumption service.

    :param HVAC_CONSUMPTION_HOST_ADDRESS: Optional argument to supply host address for given service. Otherwise,
        set as environment variable.
    :return: grpc Stub object.

    """

    if HVAC_CONSUMPTION_HOST_ADDRESS is None:
        HVAC_CONSUMPTION_HOST_ADDRESS = os.environ["HVAC_CONSUMPTION_HOST_ADDRESS"]

    credentials = grpc.ssl_channel_credentials()
    hvac_consumption_channel = grpc.secure_channel(HVAC_CONSUMPTION_HOST_ADDRESS, credentials)
    return hvac_consumption_pb2_grpc.ConsumptionHVACStub(hvac_consumption_channel)


def get_hvac_consumption(hvac_consumption_stub, building, zone):
    hvac_consumption_response = hvac_consumption_stub.GetConsumption(
        hvac_consumption_pb2.Request(building=building, zone=zone))

    hvac_consumption_final = {NO_ACTION: 0,
                              HEATING_ACTION: hvac_consumption_response.heating_consumption,
                              COOLING_ACTION: hvac_consumption_response.cooling_consumption,
                              FAN: hvac_consumption_response.ventilation_consumption,
                              TWO_STAGE_HEATING_ACTION: hvac_consumption_response.heating_consumption_stage_two,
                              TWO_STAGE_COOLING_ACTION: hvac_consumption_response.cooling_consumption_stage_two}

    return hvac_consumption_final


# Outdoor temperature functions
def get_outdoor_historic_stub(OUTDOOR_TEMPERATURE_HISTORICAL_HOST_ADDRESS=None):
    """Get the stub to interact with the outdoor_temperature_historical service.

    :param OUTDOOR_TEMPERATURE_HISTORICAL_HOST_ADDRESS: Optional argument to supply host address for given service.
        Otherwise, set as environment variable.
    :return: grpc Stub object.

    """

    if OUTDOOR_TEMPERATURE_HISTORICAL_HOST_ADDRESS is None:
        OUTDOOR_TEMPERATURE_HISTORICAL_HOST_ADDRESS = os.environ["OUTDOOR_TEMPERATURE_HISTORICAL_HOST_ADDRESS"]

    credentials = grpc.ssl_channel_credentials()
    outdoor_historic_channel = grpc.secure_channel(OUTDOOR_TEMPERATURE_HISTORICAL_HOST_ADDRESS, credentials)
    return outdoor_temperature_historical_pb2_grpc.OutdoorTemperatureStub(outdoor_historic_channel)


def get_outdoor_temperature_historic(outdoor_historic_stub, building, start, end, window):
    """Gets historic outdoor temperature as pd.series.

    :param indoor_historic_stub: grpc stub for historic outdoor temperature microservice
    :param building: (str) building name
    :param zone: (str) zone name
    :param start: (datetime timezone aware)
    :param end: (datetime timezone aware)
    :param window: (str) the interval in which to split the data.
    :return: pd.series valus=float, index=time

    """
    start_unix = int(start.timestamp() * 1e9)
    end_unix = int(end.timestamp() * 1e9)
    window_seconds = get_window_in_sec(window)

    # call service
    historic_outdoor_response = outdoor_historic_stub.GetTemperature(
        outdoor_temperature_historical_pb2.TemperatureRequest(
            building=building, start=int(start_unix), end=int(end_unix), window=window))

    # process data
    historic_outdoor_final = pd.Series(index=pd.date_range(start, end, freq=str(window_seconds) + "S"))[:-1]
    for msg in historic_outdoor_response.temperatures:
        msg_datetime = datetime.datetime.utcfromtimestamp(msg.time / 1e9).replace(tzinfo=pytz.utc).astimezone(
            tz=start.tzinfo)
        historic_outdoor_final.loc[msg_datetime] = msg.temperature

    return historic_outdoor_final


