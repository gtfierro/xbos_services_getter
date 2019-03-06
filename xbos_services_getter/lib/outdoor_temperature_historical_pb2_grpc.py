# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

import outdoor_temperature_historical_pb2 as outdoor__temperature__historical__pb2


class OutdoorTemperatureStub(object):
  """The temperature service definition.
  """

  def __init__(self, channel):
    """Constructor.

    Args:
      channel: A grpc.Channel.
    """
    self.GetTemperature = channel.unary_unary(
        '/outdoor_temperature_historical.OutdoorTemperature/GetTemperature',
        request_serializer=outdoor__temperature__historical__pb2.TemperatureRequest.SerializeToString,
        response_deserializer=outdoor__temperature__historical__pb2.TemperatureReply.FromString,
        )


class OutdoorTemperatureServicer(object):
  """The temperature service definition.
  """

  def GetTemperature(self, request, context):
    """A simple RPC.

    Sends the outside temperature for a given building, within a duration (start, end), and a requested window
    An error  is returned if there are no temperature for the given request
    """
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


def add_OutdoorTemperatureServicer_to_server(servicer, server):
  rpc_method_handlers = {
      'GetTemperature': grpc.unary_unary_rpc_method_handler(
          servicer.GetTemperature,
          request_deserializer=outdoor__temperature__historical__pb2.TemperatureRequest.FromString,
          response_serializer=outdoor__temperature__historical__pb2.TemperatureReply.SerializeToString,
      ),
  }
  generic_handler = grpc.method_handlers_generic_handler(
      'outdoor_temperature_historical.OutdoorTemperature', rpc_method_handlers)
  server.add_generic_rpc_handlers((generic_handler,))
