import React, {useState} from 'react';

import { TitleCard, WithEndpoint } from 'odin-react';
import ToggleSwitch from '../ToggleSwitch';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import Button from 'react-bootstrap/Button';

import InputGroup from 'react-bootstrap/InputGroup';
import Form from 'react-bootstrap/Form';

const EndPointFormControl = WithEndpoint(Form.Control);
const EndPointToggle = WithEndpoint(ToggleSwitch);
const EndPointButton = WithEndpoint(Button);

function PiezoStage(props){
  const {name, data, kinesisEndPoint, dataPath} = props;

  const [targetPosition, setTargetPosition] = useState(data.position.set_target_pos ?? '');
  const handleTargetChange = (event) => {
    setTargetPosition(event.target.value);
  };

  return (
    <TitleCard title={"Motor "+name}>
    <Row>
      <Col xs={7}>
        <Row>
          <Col xs={6}>
            <InputGroup>
              <InputGroup.Text>Steps</InputGroup.Text>
                <InputGroup.Text>{data.position.current_pos}</InputGroup.Text>
            </InputGroup>
          </Col>
          <Col xs={6}>
            <InputGroup>
              <InputGroup.Text>Target</InputGroup.Text>
                <Form.Control
                  type="number"
                  value={targetPosition}
                  event_type="enter"
                  onChange={handleTargetChange}
                  disabled={data.moving}
                >
                </Form.Control>
                <EndPointButton
                  endpoint={kinesisEndPoint}
                  fullpath={dataPath+"/position/set_target_pos"}
                  event_type="click"
                  value={targetPosition}
                >
                  Move
                </EndPointButton>

            </InputGroup>
          </Col>
        </Row>
        <Row className='mt-3'>
          <Col>
            details
          </Col>
          <Col>
          Jog settings
            <InputGroup>
              <InputGroup.Text>
                Step size fwd
              </InputGroup.Text>
              <EndPointFormControl
                  endpoint={kinesisEndPoint}
                  fullpath={dataPath+"/jog/step_size_fwd"}
                  type="number"
                  event_type="enter"
                  value={data.jog.step_size_fwd}
              />
            </InputGroup>
            <InputGroup>
              <InputGroup.Text>
                Step size rev
              </InputGroup.Text>
              <EndPointFormControl
                  endpoint={kinesisEndPoint}
                  fullpath={dataPath+"/jog/step_size_rev"}
                  type="number"
                  event_type="enter"
                  value={data.jog.step_size_fwd}
              />
            </InputGroup>
            <InputGroup>
              <InputGroup.Text>
                Step rate
              </InputGroup.Text>
              <EndPointFormControl
                  endpoint={kinesisEndPoint}
                  fullpath={dataPath+"/jog/step_rate"}
                  type="number"
                  event_type="enter"
                  value={data.jog.step_rate}
              />
            </InputGroup>
            <InputGroup>
              <InputGroup.Text>
                Accel.
              </InputGroup.Text>
              <EndPointFormControl
                  endpoint={kinesisEndPoint}
                  fullpath={dataPath+"/jog/accel"}
                  type="number"
                  event_type="enter"
                  value={data.jog.accel}
              />
            </InputGroup>
          </Col>
        </Row>
      </Col>
      <Col xs={5}>
        <Row>
          <Col xs={6} className='mr-3'>
            <Row>
              <EndPointButton
                endpoint={kinesisEndPoint}
                fullpath={dataPath+"/jog/step"}
                event_type="click"
                value={true}
              >
                Step forward
              </EndPointButton>
            </Row>
            <Row className='mt-3'>
            <EndPointButton
                endpoint={kinesisEndPoint}
                fullpath={dataPath+"/jog/step"}
                event_type="click"
                value={false}
            >
              Step backward
            </EndPointButton>
            </Row>
          </Col>
          <Col xs={6} className="ml-2">
            <Row>
              <EndPointButton
                endpoint={kinesisEndPoint}
                fullpath={dataPath+"/position/home"}
                event_type="click"
                value={true}
              >Zero</EndPointButton>
            </Row>
            <Row className='mt-3'>
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
            <Row>
              Identify
            </Row>
            <Row>
              etc.
            </Row>
          </Col>
        </Row>
      </Col>
    </Row>
    </TitleCard>
  );
}

export default PiezoStage;
