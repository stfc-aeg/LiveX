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
        <Col xs={6} xxl={4}>
          <PidControl
            furnaceEndPoint={furnaceEndPoint}
            connectedPuttingDisable={connectedPuttingDisable}
            title="Upper Heater (A) Controls"
            pid="pid_a">
          </PidControl>

          <PidControl
            furnaceEndPoint={furnaceEndPoint}
            connectedPuttingDisable={connectedPuttingDisable}
            title="Lower Heater (B) Controls"
            pid="pid_b">
          </PidControl>

        </Col>
        <Col md={6} xxl={4}>

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