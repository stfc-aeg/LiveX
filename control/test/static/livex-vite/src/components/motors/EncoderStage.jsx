import React, {useState} from 'react';

import { TitleCard, WithEndpoint } from 'odin-react';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import Button from 'react-bootstrap/esm/Button';

import InputGroup from 'react-bootstrap/InputGroup';
import Form from 'react-bootstrap/Form';
import Accordion from 'react-bootstrap/Accordion';

import { floatingLabelStyle, floatingInputStyle } from '../../utils.js'
import FloatingLabel from 'react-bootstrap/FloatingLabel';

const EndPointFormControl = WithEndpoint(Form.Control);
const EndPointFormCheck = WithEndpoint(Form.Check);
const EndPointButton = WithEndpoint(Button);

function EncoderStage(props){
  const {name, data, kinesisEndPoint, dataPath} = props;

  const [targetPosition, setTargetPosition] = useState(data.position.set_target_pos ?? '');
  const handleTargetChange = (event) => {
    setTargetPosition(event.target.value);
  };

  return (
    <TitleCard title={"Motor "+name}>
    <Row>
      <Col xs={4}>
        <Row>
          <EndPointButton
            endpoint={kinesisEndPoint}
            fullpath={dataPath+"/position/set_target_pos"}
            event_type="click"
            value={targetPosition}
          >
            Move to target
          </EndPointButton>
        </Row>
        <Row className="mt-3">
          <Col>
            <EndPointButton
              endpoint={kinesisEndPoint}
              fullpath={dataPath + "/jog/step"}
              event_type="click"
              value={true}
            >
              Step forward
            </EndPointButton>
          </Col>
          <Col>
            <EndPointButton
              endpoint={kinesisEndPoint}
              fullpath={dataPath + "/jog/step"}
              event_type="click"
              value={false}
            >
              Step backward
            </EndPointButton>
          </Col>
        </Row>
        <Row className='mt-3'>
          <EndPointButton
            endpoint={kinesisEndPoint}
            fullpath={dataPath+"/position/home"}
            event_type="click"
            value={true}
          >
             Home
          </EndPointButton>
        </Row>
        <Row className="mt-3">
          <EndPointButton
            endpoint={kinesisEndPoint}
            fullpath={dataPath+"/position/stop"}
            event_type="click"
            variant="danger"
            value={true}
          >
            Stop movement
          </EndPointButton>
        </Row>
      </Col>
      <Col xs={4}>
        <Row>
          <Col>
            <label>Position (mm)</label>
          </Col>
        </Row>
        <Row>
          <Col>
            <FloatingLabel
              label="Current:">
                <Form.Control
                  plaintext
                  readOnly
                  style={{
                    width: "100%",
                    border: '1px solid lightblue',
                    backgroundColor: '#e0f7ff',
                    borderRadius: '0.375rem'
                  }}
                  value={data.position.current_pos}
                />
            </FloatingLabel>
          </Col>
          <Col>
            <FloatingLabel
              label="Target">
                <Form.Control
                  value={targetPosition}
                  style={floatingInputStyle}
                  onChange={handleTargetChange}
                  disabled={data.moving}
                />
            </FloatingLabel>
          </Col>
        </Row>
        <Row className='mt-3'>
          <Col>
            <FloatingLabel
              label="Upper limit">
                <EndPointFormControl
                  endpoint={kinesisEndPoint}
                  fullpath={dataPath + "/limits/upper_limit"}
                  style={floatingInputStyle}
                />
            </FloatingLabel>
          </Col>
          <Col>
            <FloatingLabel
              label="Lower limit">
                <EndPointFormControl
                  endpoint={kinesisEndPoint}
                  fullpath={dataPath + "/limits/lower_limit"}
                  style={floatingInputStyle}
                />
            </FloatingLabel>
          </Col>
        </Row>
      </Col>
      <Col xs={4}>
        <Row className='mt-2'>
          <Accordion >
            <Accordion.Item eventKey="0">
              <Accordion.Header>Jog/step settings</Accordion.Header>
              <Accordion.Body>
                <Row>
                  <Col>
                    <EndPointButton
                      endpoint={kinesisEndPoint}
                      fullpath={dataPath+"/jog/reverse"}
                      value={data.jog.reverse ? false : true}
                      event_type="click"
                      text="reverse forward/back"
                    >
                      {data.jog.reverse ? "Unreverse" : "Reverse"} forward/back
                    </EndPointButton>
                  </Col>
                </Row>
                <InputGroup className="mt-2">
                  <InputGroup.Text>Step</InputGroup.Text>
                  <EndPointFormControl
                    endpoint={kinesisEndPoint}
                    fullpath={dataPath + "/jog/step_size"}
                    type="number"
                    event_type="enter"
                    value={data.jog.step_size}
                  />
                </InputGroup>
                <InputGroup className="mt-2">
                  <InputGroup.Text>Max vel.</InputGroup.Text>
                  <EndPointFormControl
                    endpoint={kinesisEndPoint}
                    fullpath={dataPath + "/jog/max_vel"}
                    type="number"
                    event_type="enter"
                    value={data.jog.max_vel}
                  />
                </InputGroup>
                <InputGroup className="mt-2">
                  <InputGroup.Text>Accel.</InputGroup.Text>
                  <EndPointFormControl
                    endpoint={kinesisEndPoint}
                    fullpath={dataPath + "/jog/accel"}
                    type="number"
                    event_type="enter"
                    value={data.jog.accel}
                  />
                </InputGroup>
              </Accordion.Body>
            </Accordion.Item>
          </Accordion>
        </Row>
      </Col>
    </Row>
    </TitleCard>
  );
}

export default EncoderStage;
