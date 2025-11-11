import React from 'react';

import { WithEndpoint } from 'odin-react';
import Button from 'react-bootstrap/Button';
import Container from 'react-bootstrap/Container';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';

import PidControl from './PidControl';
import ThermalGradient from './ThermalGradient';
import AutoSetPointControl from './AutoSetPointControl';
import InfoPanel from './InfoPanel';
import FurnaceRecording from './FurnaceRecording';

function FurnacePage(props){
    const {furnaceEndPoint} = props;
    const {connectedPuttingDisable} = props;

    const EndPointButton = WithEndpoint(Button);

    return (
    <Row>
        <Container>
          <Row className="d-flex justify-content-between">
            <Col xs="auto">
              <EndPointButton
                endpoint={furnaceEndPoint}
                value={true}
                fullpath="status/reconnect"
                disabled={!connectedPuttingDisable}
                variant={furnaceEndPoint.data.status?.connected ? "primary" : "danger"}>
                {furnaceEndPoint.data.status?.connected ? 'Connected' : 'Reconnect'}
              </EndPointButton>
            </Col>
            <Col xs="auto">
              <EndPointButton
                endpoint={furnaceEndPoint}
                value={true}
                fullpath="status/full_stop"
                disabled={connectedPuttingDisable}
                variant='danger'>Disable all outputs
              </EndPointButton>
            </Col>
          </Row>
        </Container>
        <Col xs={12} md={6}>
          <PidControl
            furnaceEndPoint={furnaceEndPoint}
            connectedPuttingDisable={connectedPuttingDisable}
            title="Upper Heater Controls"
            pid="pid_upper">
          </PidControl>

          <PidControl
            furnaceEndPoint={furnaceEndPoint}
            connectedPuttingDisable={connectedPuttingDisable}
            title="Lower Heater Controls"
            pid="pid_lower">
          </PidControl>

          {
            furnaceEndPoint.data.status?.allow_solo_acquisition ?
            <FurnaceRecording
              furnaceEndPoint={furnaceEndPoint}
              connectedPuttingDisable={connectedPuttingDisable}
            />
            :
            <></>
          }

        </Col>
        <Col md={6}>

          <ThermalGradient
            furnaceEndPoint={furnaceEndPoint}
            connectedPuttingDisable={connectedPuttingDisable}>
          </ThermalGradient>

          <AutoSetPointControl
            furnaceEndPoint={furnaceEndPoint}
            connectedPuttingDisable={connectedPuttingDisable}>
          </AutoSetPointControl>

          <InfoPanel
            furnaceEndPoint={furnaceEndPoint}
            connectedPuttingDisable={connectedPuttingDisable}>
          </InfoPanel>
        </Col>
    </Row>
    )
}
export default FurnacePage;