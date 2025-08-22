import React from 'react';
import EncoderStage from './EncoderStage.jsx';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';

import Button from 'react-bootstrap/Button';

import { TitleCard, WithEndpoint } from 'odin-react';


function KdcController(props) {
  const {name, motors, kinesisEndPoint} = props;

  const EndPointButton = WithEndpoint(Button);

  return (
    <Row className="controller">
      <Row>
        <Col xs={2}>
          Controller: {name}
        </Col>
        <Col xs="auto">
          <EndPointButton
            endpoint={kinesisEndPoint}
            value={true}
            fullpath={`controllers/${name}/connected`}
            variant={kinesisEndPoint.data?.controllers[name].connected ? "primary" : "danger"}
            disabled={kinesisEndPoint.data?.controllers[name].connected}>
            {kinesisEndPoint.data?.controllers[name].connected ? 'Connected' : 'Reconnect'}
          </EndPointButton>
        </Col>
      </Row>
      
      {Object.entries(motors).map(([motorName, motorData]) => (
        <EncoderStage
          key={motorName}
          name={motorName}
          data={motorData}
          kinesisEndPoint={kinesisEndPoint}
          dataPath={`controllers/${name}/motors/${motorName}`}
        />
      ))}
    </Row>
  );
}

export default KdcController;