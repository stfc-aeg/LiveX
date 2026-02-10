import React from 'react';

import { TitleCard, WithEndpoint, useAdapterEndpoint } from 'odin-react';
import Button from 'react-bootstrap/Button';
import Container from 'react-bootstrap/Container';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';

import PidControl from './PidControl';
import ThermalGradient from './ThermalGradient';
import AutoSetPointControl from './AutoSetPointControl';
import InfoPanel from './InfoPanel';
import FurnaceRecording from './FurnaceRecording';
import PidOverride from './PidOverride';

function FurnacePage(props){
    
    const endpoint_url = import.meta.env.VITE_ENDPOINT_URL;

    const furnaceEndPoint = useAdapterEndpoint('furnace', endpoint_url, 500);
    const EndPointButton = WithEndpoint(Button);

    const connectedDisable = (!(furnaceEndPoint.data.status?.connected || false))

    return (
    <Row>
        <Container>
          <Row className="d-flex justify-content-between">
            <Col xs="auto">
              <EndPointButton
                endpoint={furnaceEndPoint}
                value={true}
                fullpath="status/reconnect"
                disabled={!connectedDisable}
                variant={furnaceEndPoint.data.status?.connected ? "primary" : "danger"}>
                {furnaceEndPoint.data.status?.connected ? 'Connected' : 'Reconnect'}
              </EndPointButton>
            </Col>
            <Col xs="auto">
              <EndPointButton
                endpoint={furnaceEndPoint}
                value={true}
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
            furnaceEndPoint.data.status?.allow_pid_override ?
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

          {
            furnaceEndPoint.data.status?.allow_solo_acquisition ?
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

          <InfoPanel/>
        </Col>
    </Row>
    )
}
export default FurnacePage;