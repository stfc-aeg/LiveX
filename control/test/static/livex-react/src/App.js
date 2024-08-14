import './App.css';

import 'odin-react/dist/index.css'
import 'bootstrap/dist/css/bootstrap.min.css';

import Container from 'react-bootstrap/Container';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import Button from 'react-bootstrap/Button';

import TemperatureGraph from './components/furnace/TemperatureGraph';
import PidControl from './components/furnace/PidControl';
import ThermalGradient from './components/furnace/ThermalGradient';
import AutoSetPointControl from './components/furnace/AutoSetPointControl';
import Motor from './components/furnace/Motor';
import React from "react";
import { TitleCard, StatusBox, OdinApp } from 'odin-react';
import { WithEndpoint, useAdapterEndpoint } from 'odin-react';
import Metadata from './components/setup/Metadata';
import Cameras from './components/cameras/Cameras';
import Trigger from './components/setup/Trigger';

const EndPointButton = WithEndpoint(Button);

function App(props) {

  const endpoint_url = process.env.REACT_APP_ENDPOINT_URL

  const furnaceEndPoint = useAdapterEndpoint('furnace', endpoint_url, 1000);
  const connectedPuttingDisable = (!(furnaceEndPoint.data.status?.connected || false)) || (furnaceEndPoint.loading === "putting")

  return (
    <OdinApp title="LiveX Controls" navLinks={["Metadata and Setup", "Sequencing", "Furnace Control", "Camera Control", "Monitoring"]}>
    <Col>
      <Metadata
        endpoint_url={endpoint_url}
        connectedPuttingDisable={connectedPuttingDisable}>
      </Metadata>
      <Trigger
        endpoint_url={endpoint_url}>
      </Trigger>
    </Col>
    <Col>
      sequencer
    </Col>
    <Col>
    <Container>
      <Col>
        <Row className="d-flex justify-content-between">
          <Col xs="auto">
            <EndPointButton
              endpoint={furnaceEndPoint}
              value={true}
              fullpath="status/reconnect"
              event_type="click"
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
              event_type="click"
              disabled={connectedPuttingDisable}
              variant='danger'>Disable all outputs
            </EndPointButton>
          </Col>
        </Row>

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

      <TitleCard title="'Acquisition card'">
        <Container>
          <Row>
          <EndPointButton
            endpoint={furnaceEndPoint}
            fullpath={"tcp/acquire"}
            value={furnaceEndPoint.data.tcp?.acquire ? false : true}
            event_type="click"
            disable={connectedPuttingDisable}
            variant={furnaceEndPoint.data.tcp?.acquire ? "danger" : "success" }>
              {furnaceEndPoint.data.tcp?.acquire ? "Stop acquisition" : "Start acquisition"}
          </EndPointButton>
          <Col>
          <Row>
            <StatusBox as="span" type="info" label="reading">
              {furnaceEndPoint.data.tcp?.tcp_reading?.counter}{furnaceEndPoint.data.tcp?.tcp_reading?.temperature_a}
            </StatusBox>
            </Row>
            </Col>
          </Row>
        </Container>

      </TitleCard>

      <ThermalGradient
        furnaceEndPoint={furnaceEndPoint}
        connectedPuttingDisable={connectedPuttingDisable}>
      </ThermalGradient>

      <AutoSetPointControl
        furnaceEndPoint={furnaceEndPoint}
        connectedPuttingDisable={connectedPuttingDisable}>
      </AutoSetPointControl>

      </Col>

    </Container>
    <Col>
      <Motor
        furnaceEndPoint={furnaceEndPoint}
        connectedPuttingDisable={connectedPuttingDisable}>
      </Motor>
      </Col>
    </Col>
    <Col>
    <Cameras
      endpoint_url={endpoint_url}
      connectedPuttingDisable={connectedPuttingDisable}>
    </Cameras>
    </Col>
    <Col>
    <TemperatureGraph
      furnaceEndPoint={furnaceEndPoint}>
    </TemperatureGraph>
    </Col>
    </OdinApp>
  );
}

export default App;