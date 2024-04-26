import './App.css';

import 'odin-react/dist/index.css'
import 'bootstrap/dist/css/bootstrap.min.css';

import Container from 'react-bootstrap/Container';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import Button from 'react-bootstrap/Button';

import TemperatureGraph from './components/TemperatureGraph';
import PidControl from './components/PidControl';
import ThermalGradient from './components/ThermalGradient';
import AutoSetPointControl from './components/AutoSetPointControl';
import Motor from './components/Motor';
import React from "react";
import { TitleCard, StatusBox, OdinApp } from 'odin-react';
import { WithEndpoint, useAdapterEndpoint } from 'odin-react';
import Metadata from './components/Metadata';
import Cameras from './components/Cameras';

const EndPointButton = WithEndpoint(Button);

function App(props) {

  const liveXEndPoint = useAdapterEndpoint('furnace', 'http://localhost:8888', 500);
  const connectedPuttingDisable = (!(liveXEndPoint.data.status?.connected || false)) || (liveXEndPoint.loading == "putting")

  return (
    <OdinApp title="LiveX Controls" navLinks={["furnace control", "metadata", "setup", "sequencing", "camera control", "monitoring"]}>
    <Col>
    <Container>
      <Col>
      <EndPointButton
        endpoint={liveXEndPoint}
        value={true}
        fullpath="status/reconnect"
        event_type="click"
        disabled={!connectedPuttingDisable}
        variant={liveXEndPoint.data.status?.connected ? "primary" : "danger"}>
        {liveXEndPoint.data.status?.connected ? 'Connected' : 'Reconnect'}
      </EndPointButton>

      <PidControl
        liveXEndPoint={liveXEndPoint}
        connectedPuttingDisable={connectedPuttingDisable}
        title="Upper Heater (A) Controls"
        pid="pid_a">
      </PidControl>

      <PidControl
        liveXEndPoint={liveXEndPoint}
        connectedPuttingDisable={connectedPuttingDisable}
        title="Lower Heater (B) Controls"
        pid="pid_b">
      </PidControl>

      <TitleCard title="test card">
        <Container>
          <Row>
          <EndPointButton
            endpoint={liveXEndPoint}
            fullpath={"tcp/acquire"}
            value={liveXEndPoint.data.tcp?.acquire ? false : true}
            event_type="click"
            disable={connectedPuttingDisable}
            variant={liveXEndPoint.data.tcp?.acquire ? "danger" : "success" }>
              {liveXEndPoint.data.tcp?.acquire ? "Stop acquisition" : "Start acquisition"}
          </EndPointButton>
          <Col>
          <Row>
            <StatusBox as="span" type="info" label="reading">
              {liveXEndPoint.data.tcp?.tcp_reading?.counter} {liveXEndPoint.data.tcp?.tcp_reading?.temperature_a}
            </StatusBox>
            </Row>
            </Col>
          </Row>
        </Container>

      </TitleCard>

      <ThermalGradient
        liveXEndPoint={liveXEndPoint}
        connectedPuttingDisable={connectedPuttingDisable}>
      </ThermalGradient>

      <AutoSetPointControl
        liveXEndPoint={liveXEndPoint}
        connectedPuttingDisable={connectedPuttingDisable}>
      </AutoSetPointControl>

      </Col>

    </Container>
    <Col>
    <Motor
        liveXEndPoint={liveXEndPoint}
        connectedPuttingDisable={connectedPuttingDisable}>
      </Motor>
      </Col>
    </Col>
    <Col>
      <Metadata
        liveXEndPoint={liveXEndPoint}
        connectedPuttingDisable={connectedPuttingDisable}>
      </Metadata>
    </Col>
    <Col>
      setup
    </Col>
    <Col>
      sequencer
    </Col>
    <Col>
      camera control
    <Cameras
      connectedPuttingDisable={connectedPuttingDisable}>
    </Cameras>

    </Col>
    <Col>
    <TemperatureGraph
      liveXEndPoint={liveXEndPoint}
      connectedPuttingDisable={connectedPuttingDisable}>
    </TemperatureGraph>
    </Col>
    </OdinApp>
  );
}

export default App;