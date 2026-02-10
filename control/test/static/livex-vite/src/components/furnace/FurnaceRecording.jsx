import React from 'react';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import InputGroup from 'react-bootstrap/InputGroup';
import Button from 'react-bootstrap/Button';
import { TitleCard, WithEndpoint } from 'odin-react';
import { checkNullNoDp  } from '../../utils';

const EndPointButton = WithEndpoint(Button);

function FurnaceRecording(props) {
    const {furnaceEndPoint} = props;

    // Fixing the label width of the display labels so that they're consistent
    // ~6px per character. 
    const labelWidth = 80;

  return (
    <TitleCard title={
      <Row>
        <Col xs={3} className="d-flex align-items-center" style={{fontSize:'1.3rem'}}>Furnace-only acquisition</Col>
      </Row>
    }>
      <Row>
        <Col xs={4}>
          <InputGroup>
            <InputGroup.Text style={{width:labelWidth}}>
              # Readings
            </InputGroup.Text>
            <InputGroup.Text style={{
              width: labelWidth,
              border: '1px solid lightblue',
              backgroundColor: '#e0f7ff'
            }}>
              {checkNullNoDp(furnaceEndPoint.data.tcp?.tcp_reading?.counter)}
            </InputGroup.Text>
          </InputGroup>
        </Col>
        <Col xs={4}>
          <InputGroup>
            <InputGroup.Text style={{width: labelWidth}}>
              Latest temp.
            </InputGroup.Text>
            <InputGroup.Text style={{
              width: labelWidth,
              border: '1px solid lightblue',
              backgroundColor: '#e0f7ff'
            }}>
              {checkNullNoDp(furnaceEndPoint.data.tcp?.tcp_reading?.temperature_a)}
            </InputGroup.Text>
          </InputGroup>
        </Col>
      </Row>
      <Row className="mt-3">
        <EndPointButton
          endpoint={furnaceEndPoint}
          fullpath={"tcp/acquire"}
          value={furnaceEndPoint.data.tcp?.acquire ? false : true}
          event_type="click"
          variant={furnaceEndPoint.data.tcp?.acquire ? "danger" : "success" }>
          {furnaceEndPoint.data.tcp?.acquire ? "Stop furnace recording" : "Record (only) furnace data"}
        </EndPointButton>
      </Row>
    </TitleCard>
  )
}
export default FurnaceRecording;