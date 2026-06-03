
import { FurnaceEndpointTypes } from '../../EndpointTypes';

import { Col, Row, Button, Container } from 'react-bootstrap';
import { TitleCard, WithEndpoint, useAdapterEndpoint } from 'odin-react';

import PidControl from './PidControl';
import ThermalGradient from './ThermalGradient';
import AutoSetPointControl from './AutoSetPointControl';
import InfoPanel from './InfoPanel';
import FurnaceRecording from './FurnaceRecording';
import PidOverride from './PidOverride';
import FurnaceMeta from './FurnaceMeta';

function FurnacePage(){
    
    const endpoint_url = import.meta.env.VITE_ENDPOINT_URL;

    const furnaceEndPoint = useAdapterEndpoint<FurnaceEndpointTypes>('furnace', endpoint_url, 500);
    const EndPointButton = WithEndpoint(Button);

    const connectedDisable = (!(furnaceEndPoint.data?.status?.connected || false))

    return (
      <Row>
        <Container>
          <Row className="d-flex justify-content-between">
            <Col xs="auto">
              <EndPointButton
                endpoint={furnaceEndPoint}
                value={true as any}
                fullpath="status/reconnect"
                disabled={!connectedDisable}
                variant={furnaceEndPoint.data?.status?.connected ? "primary" : "danger"}>
                {furnaceEndPoint.data?.status?.connected ? 'Connected' : 'Reconnect'}
              </EndPointButton>
            </Col>
            <Col xs="auto">
              <EndPointButton
                endpoint={furnaceEndPoint}
                value={true as any}
                fullpath="status/full_stop"
                disabled={connectedDisable}
                variant='danger'>Disable all outputs
              </EndPointButton>
            </Col>
          </Row>
        </Container>
        <Col xs={12} md={6}>
          <PidControl
            furnaceEndPoint={furnaceEndPoint}
            connectedDisable={connectedDisable}
            title="Upper Heater Controls"
            pid="pid_upper">
          </PidControl>

          <PidControl
            furnaceEndPoint={furnaceEndPoint}
            connectedDisable={connectedDisable}
            title="Lower Heater Controls"
            pid="pid_lower">
          </PidControl>

          {
            furnaceEndPoint.data?.status?.allow_pid_override ?
            <TitleCard
              title="Manual PID Override">
                <Row>
                  <label>
                    PID Override sets the output to a percentage of its maximum (0-10V), it does not require the PID to be enabled to use.
                  </label>
                </Row>
                <Row>
                  <Col>
                    <PidOverride
                      furnaceEndPoint={furnaceEndPoint}
                      connectedDisable={connectedDisable}
                      title="Upper PID"
                      pid="pid_upper"
                    />
                  </Col>
                  <Col>
                    <PidOverride
                      furnaceEndPoint={furnaceEndPoint}
                      connectedDisable={connectedDisable}
                      title="Lower PID"
                      pid="pid_lower"
                    />
                  </Col>
                </Row>
            </TitleCard> :
            <></>
          }

          <FurnaceMeta
            furnaceEndPoint={furnaceEndPoint}
            connectedDisable={connectedDisable}
          />

          {
            furnaceEndPoint.data?.status?.allow_solo_acquisition ?
            <FurnaceRecording
              furnaceEndPoint={furnaceEndPoint}
            />
            :
            <></>
          }
        </Col>
        <Col md={6}>

          <ThermalGradient
            furnaceEndPoint={furnaceEndPoint}
            connectedDisable={connectedDisable}
          />

          <AutoSetPointControl
            furnaceEndPoint={furnaceEndPoint}
            connectedDisable={connectedDisable}
          />

          <InfoPanel furnaceEndPoint={furnaceEndPoint}/>
        </Col>
      </Row>
    )
}
export default FurnacePage;